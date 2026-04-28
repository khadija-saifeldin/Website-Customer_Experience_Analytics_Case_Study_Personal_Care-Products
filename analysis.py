from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import pandas as pd
import os
import matplotlib.pyplot as plt
import seaborn as sns
import folium

app = FastAPI()

df = pd.read_csv(r"C:\Users\HP\Desktop\Website\Data.csv")

images_dir = r"C:\Users\HP\Desktop\Website\images"
os.makedirs(images_dir, exist_ok=True)

templates = Jinja2Templates(directory="templates")

Products = df[['ID','age','Location','gender','social status','Product','Product Type','Evaluation','Product compliant']]
Products

general = df[['ID', 'age', 'Location', 'gender', 'social status', 'Purchase cycle', 'Place of purchase', 'Local or imported', 'Product selection factor', 'Which of these companies do you prefer?']]
general

def create_and_save_plot(data, x, y, hue, title, xlabel, ylabel, filename, images_dir, plot_type='bar', rotation=0, orient='v'):
    plt.figure(figsize=(14, 8), facecolor=('#f7edcf'))
    if plot_type == 'bar':
        sns.barplot(data=data, x=x, y=y, hue=hue, orient=orient)
    elif plot_type == 'line':
        sns.lineplot(data=data, x=x, y=y, marker='o', palette='viridis')
    plt.title(title, fontstyle='italic')
    plt.xlabel(xlabel, fontstyle='italic')
    plt.ylabel(ylabel, fontstyle='italic')
    plt.xticks(rotation=rotation)
    plt.gca().set_facecolor('#f7edcf')
    ax = plt.gca()
    for spine in ax.spines.values():
        spine.set_edgecolor('k')
        spine.set_linewidth(1)
    plt.grid(True, which='both', linestyle='--', linewidth=0.5)
    plt.legend(title='Product', bbox_to_anchor=(1.01,1.0), loc='upper left')
    plt.savefig(os.path.join(images_dir, filename), bbox_inches='tight')
    plt.close()

def create_and_save_pie_chart(data, labels, title, filename, images_dir):
    plt.figure(figsize=(8, 8), facecolor=('#f7edcf'))
    plt.pie(data, labels=labels, autopct='%1.1f%%', startangle=140, colors=sns.color_palette('pastel'))
    plt.title(title, fontstyle='italic')
    plt.gca().set_facecolor('#f7edcf')
    plt.savefig(os.path.join(images_dir, filename), bbox_inches='tight')
    plt.close()

def analyze_product(product_name):
    df = pd.read_csv(r"C:\Users\HP\Desktop\Website\Data.csv")
    Products = df[['ID','age','Location','gender','social status','Product','Product Type','Evaluation','Product compliant']]
    Products['Product'] = Products['Product'].str.strip()
    product_data = Products[Products['Product'].str.contains(product_name, case=False, na=False)]
    
    images_dir = r"C:\Users\HP\Desktop\Website\images"
    os.makedirs(images_dir, exist_ok=True)

    product_location = product_data.pivot_table(index='Product', columns='Location', values='Evaluation', aggfunc='mean').reset_index().melt(id_vars='Product', var_name='Location', value_name='Mean Evaluation')
    create_and_save_plot(product_location, 'Location', 'Mean Evaluation', 'Product', f'Mean Evaluation of {product_name} Products by Location', 'Location', 'Mean Evaluation', f'{product_name.lower()}_location.png', images_dir)

    product_gender = product_data.pivot_table(index='Product', columns='gender', values='Evaluation', aggfunc='mean').reset_index().melt(id_vars='Product', var_name='Gender', value_name='Mean Evaluation')
    create_and_save_plot(product_gender, 'Mean Evaluation', 'Product', 'Gender', f'Mean Evaluation of {product_name} Products by Gender', 'Mean Evaluation', 'Product', f'{product_name.lower()}_gender.png', images_dir, orient='h')

    # Create pie chart for gender distribution
    gender_counts = product_data['gender'].value_counts()
    create_and_save_pie_chart(gender_counts.values, gender_counts.index, f'Gender Distribution of {product_name} Products', f'{product_name.lower()}_gender_pie.png', images_dir)

    product_type = product_data.pivot_table(index='Product', columns='Product Type', values='Evaluation', aggfunc='mean').reset_index().melt(id_vars='Product', var_name='Product Type', value_name='Mean Evaluation')
    create_and_save_plot(product_type, 'Mean Evaluation', 'Product', 'Product Type', f'Mean Evaluation of {product_name} Products by Product Type', 'Mean Evaluation', 'Product', f'{product_name.lower()}_type.png', images_dir, orient='h')

    product_age = product_data.pivot_table(index='Product', columns='age', values='Evaluation', aggfunc='mean').reset_index().melt(id_vars='Product', var_name='Age Group', value_name='Mean Evaluation')
    create_and_save_plot(product_age, 'Age Group', 'Mean Evaluation', 'Product', f'Mean Evaluation of {product_name} Products by Age Group', 'Age Group', 'Mean Evaluation', f'{product_name.lower()}_age.png', images_dir)

    return {
        "location": f"{product_name.lower()}_location.png",
        "gender": f"{product_name.lower()}_gender.png",
        "gender_pie": f"{product_name.lower()}_gender_pie.png",
        "type": f"{product_name.lower()}_type.png",
        "age": f"{product_name.lower()}_age.png"
    }

def analyze_country(country_name):
    country_data = Products[Products['Location'].str.contains(country_name, case=False, na=False)]
    
    country_location = country_data.pivot_table(index='Location', columns='Product', values='Evaluation', aggfunc='mean').reset_index().melt(id_vars='Location', var_name='Product', value_name='Mean Evaluation')
    create_and_save_plot(country_location, 'Location', 'Mean Evaluation', 'Product', f'Mean Evaluation of Products by Location in {country_name}', 'Location', 'Mean Evaluation', f'{country_name.lower()}_location.png', images_dir)

    return {
        "location": f"{country_name.lower()}_location.png"
    }

def create_map(country_name, cities):
    country_map = folium.Map(location=[20.0, 10.0], zoom_start=5)  # تعديل الموقع والزووم حسب الحاجة

    for city in cities:
        folium.Marker(
            location=[city['lat'], city['lon']],
            popup=f"<b>{city['name']}</b><br><a href='/city/{city['name']}'>View Analysis</a>",
            tooltip=city['name']
        ).add_to(country_map)

    map_path = os.path.join(images_dir, f"{country_name.lower()}_map.html")
    country_map.save(map_path)
    return map_path

@app.get("/country/{country_name}", response_class=HTMLResponse)
async def country_page(request: Request, country_name: str):
    try:
        analysis_data = analyze_country(country_name)
        cities = [
            {"name": "Riyadh", "lat": 24.7136, "lon": 46.6753},
            {"name": "Jeddah", "lat": 21.4858, "lon": 39.1925},
            {"name": "Port sudan", "lat": 19.622, "lon": 37.216},
            {"name": "Al-jazeera", "lat": 14.392, "lon": 33.530},
            {"name": "Atbara", "lat": 17.675, "lon": 33.986},
            {"name": "Gedaref", "lat": 14.04034, "lon": 35.39915},
            {"name": "Halfa", "lat": 15.31995, "lon": 35.60394},
            {"name": "Kassala", "lat": 15.411, "lon": 36.398},
            {"name": "Khartoum", "lat": 15.5642, "lon": 32.5340},
            {"name": "Dammam", "lat": 26.4349, "lon": 50.1052},
            {"name": "Alexandria", "lat": 31.1975, "lon": 29.8952},
            {"name": "Cairo", "lat": 30.0394, "lon": 31.2383},
            {"name": "Ajaman", "lat": 25.3930, "lon": 55.4466},
            {"name": "Abu Dabi", "lat": 25.2639, "lon": 55.2901},
            # أضفه المدن الأخرى هنا
        ]
        map_path = create_map(country_name, cities)
        return templates.TemplateResponse("country.html", {"request": request, "country_name": country_name, "analysis_data": analysis_data, "map_path": map_path})
    except KeyError as e:
        return JSONResponse(content={"error": f"KeyError: {e}"}, status_code=500)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.get("/city/{city_name}", response_class=HTMLResponse)
async def city_page(request: Request, city_name: str):
    try:
        city_data = Products[Products['Location'].str.contains(city_name, case=False, na=False)]
        analysis_data = analyze_product(city_data)
        return templates.TemplateResponse("city.html", {"request": request, "city_name": city_name, "analysis_data": analysis_data})
    except KeyError as e:
        return JSONResponse(content={"error": f"KeyError: {e}"}, status_code=500)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.get("/product/{product_name}", response_class=HTMLResponse)
async def product_page(request: Request, product_name: str):
    try:
        analysis_data = analyze_product(product_name)
        return templates.TemplateResponse("product.html", {"request": request, "product_name": product_name, "analysis_data": analysis_data})
    except KeyError as e:
        return JSONResponse(content={"error": f"KeyError: {e}"}, status_code=500)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.get("/explor-analysis", response_class=JSONResponse)
async def explor_analysis():
    try:
        df = pd.read_csv(r"C:\Users\HP\Desktop\Website\Data.csv")
        Products = df[['ID','age','Location','gender','social status','Product','Product Type','Evaluation','Product compliant']]
        Products['Product'] = Products['Product'].str.strip()

        images_dir = r"C:\Users\HP\Desktop\Website\images"
        os.makedirs(images_dir, exist_ok=True)

        locations = ['Sudan', 'Egypt', 'UAE', 'Qatar', 'Saudi Arabia']
        analysis_data = {}

        for location in locations:
            location_safe = location.replace(" ", "_")
            Products_Location = Products[Products['Location'].str.contains(location)]
            cities = Products_Location['Location'].unique()
            city_coords = [{"name": city.split('/')[1] if '/' in city else city, "lat": 0, "lon": 0} for city in cities]  # تعديل الإحداثيات حسب الحاجة
            map_path = create_map(location, city_coords)
            analysis_data[location_safe.lower()] = map_path


        Products_female = Products[Products['gender'].str.contains('female')]
        Products_female_T = Products_female.pivot_table(index='gender', columns='Product', values='Evaluation', aggfunc='mean').reset_index().melt(id_vars='gender', value_name='Mean Evaluation')
        create_and_save_plot(Products_female_T, 'Product', 'Mean Evaluation', 'gender', 'Evaluation of Products by Females', 'Product', 'Mean Evaluation', 'evaluation_by_product_for_female_line_plot.png', images_dir, plot_type='line', rotation=90)

        Products_male = Products[Products['gender'].str.lower() == 'male']
        Products_male_T = Products_male.pivot_table(index='gender', columns='Product', values='Evaluation', aggfunc='mean').reset_index().melt(id_vars='gender', value_name='Mean Evaluation')
        create_and_save_plot(Products_male_T, 'Product', 'Mean Evaluation', 'gender', 'Evaluation of Products by Males', 'Product', 'Mean Evaluation', 'evaluation_by_product_for_male_line_plot.png', images_dir, plot_type='line', rotation=45)

        analysis_data = {
            "sudan": "evaluation_by_product_in_sudan.png",
            "egypt": "evaluation_by_product_in_egypt.png",
            "uae": "evaluation_by_product_in_uae.png",
            "qatar": "evaluation_by_product_in_qatar.png",
            "Saudi_Arabia": "evaluation_by_product_in_saudi_arabia.png",
            "female": "evaluation_by_product_for_female_line_plot.png",
            "male": "evaluation_by_product_for_male_line_plot.png"
        }
    

        return JSONResponse(content=analysis_data)
    except KeyError as e:
        logger.error(f"KeyError: {e}")
        return JSONResponse(content={"error": f"KeyError: {e}"}, status_code=500)
    except Exception as e:
        logger.error(f"Error processing analysis: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/nivea-analysis", response_class=JSONResponse)
async def nivea_analysis():
    try:
        analysis_data = analyze_product("Nivea")
        return JSONResponse(content=analysis_data)
    except KeyError as e:
        return JSONResponse(content={"error": f"KeyError: {e}"}, status_code=500)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
