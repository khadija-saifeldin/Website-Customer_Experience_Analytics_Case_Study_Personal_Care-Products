from fastapi import FastAPI, Query, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware  
import uvicorn
import pandas as pd
import logging
import os
import matplotlib.pyplot as plt
import seaborn as sns
import folium

from database import SessionLocal, engine, Base, User, Product, UserProductRating

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this to your needs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure session middleware
app.add_middleware(SessionMiddleware, secret_key="your_secret_key")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

templates = Jinja2Templates(directory="templates")

app.mount("/images", StaticFiles(directory="C:/Users/HP/Desktop/Website/images"), name="images")

Base.metadata.create_all(bind=engine)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_and_save_plot(data, x, y, hue, title, xlabel, ylabel, filename, images_dir, plot_type='bar', rotation=0, orient='v'):
    plt.figure(figsize=(14, 8), facecolor=('#f7edcf'))
    if plot_type == 'bar':
        sns.barplot(data=data, x=x, y=y, hue=hue, orient=orient)
    elif plot_type == 'line':
        sns.lineplot(data=data, x=x, y=y,marker='o', palette='viridis')
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
    create_and_save_plot(country_location, 'Location', 'Mean Evaluation', 'Product', f'Mean Evaluation of Products by Location in {country_name}', 'Location', 'Mean Evaluation', f'{country_name.lower()}_location.png')

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

@app.get("/", response_class=HTMLResponse)
async def read_index(request: Request):
    username = request.session.get("username")
    return templates.TemplateResponse("index2.html", {"request": request, "username": username})

@app.get("/login", response_class=HTMLResponse)
async def read_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/contact", response_class=HTMLResponse)
async def read_contact(request: Request):
    return templates.TemplateResponse("contact.html", {"request": request})

@app.get("/all-products", response_class=HTMLResponse)
async def read_products(request: Request):
    return templates.TemplateResponse("products.html", {"request": request})

@app.get("/search")
async def search_product(product_name: str):
    if "/" in product_name:
        country, city = product_name.split("/", 1)
        return RedirectResponse(url=f"/city/{city.strip()}")
    else:
        return RedirectResponse(url=f"/product/{product_name.strip()}")


@app.get("/product/{product_name}", response_class=HTMLResponse)
async def product_page(request: Request, product_name: str):
    try:
        analysis_data = analyze_product(product_name)
        return templates.TemplateResponse("product.html", {"request": request, "product_name": product_name, "analysis_data": analysis_data})
    except KeyError as e:
        return JSONResponse(content={"error": f"KeyError: {e}"}, status_code=500)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
    
@app.get("/country/{country_name}", response_class=HTMLResponse)
async def country_page(request: Request, country_name: str):
    try:
        analysis_data = analyze_country(country_name)
        cities = [
            {"name": "Riyadh", "lat": 24.7136, "lon": 46.6753},
            {"name": "Jeddah", "lat": 21.4858, "lon": 39.1925},
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
        city_data = df[df['Location'].str.contains(city_name, case=False, na=False)]
        analysis_data = analyze_product(city_data)
        return templates.TemplateResponse("city.html", {"request": request, "city_name": city_name, "analysis_data": analysis_data})
    except KeyError as e:
        return JSONResponse(content={"error": f"KeyError: {e}"}, status_code=500)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/explor", response_class=HTMLResponse)
async def read_explor(request: Request):
    return templates.TemplateResponse("explor.html", {"request": request})

@app.get("/explor-analysis", response_class=JSONResponse)
async def explor_analysis():
    try:
        df = pd.read_csv(r"C:\Users\HP\Desktop\Website\Data.csv")
        Products = df[['ID','age','Location','gender','social status','Product','Product Type','Evaluation','Product compliant']]
        Products['Product'] = Products['Product'].str.strip()

        images_dir = r"C:\Users\HP\Desktop\Website\images"
        os.makedirs(images_dir, exist_ok=True)

        locations = ['Sudan', 'Egypt', 'UAE', 'Qatar']
        for location in locations:
            location_safe = location.replace(" ", "_")
            Products_Location = Products[Products['Location'].str.contains(location)]
            Products_Location_T = Products_Location.pivot_table(index='Location', columns='Product', values='Evaluation', aggfunc='mean').reset_index().melt(id_vars='Location', var_name='Product', value_name='Mean Evaluation')
            create_and_save_plot(Products_Location_T, 'Location', 'Mean Evaluation', 'Product', f'Evaluation by Product in {location}', 'Location', 'Mean Evaluation', f'evaluation_by_product_in_{location_safe.lower()}.png', images_dir, rotation=15)

        Products_Saudi_Arabia = Products[Products['Location'].str.contains('Saudi Arabia')]
        Products_Saudi_Arabia_T = Products_Saudi_Arabia.pivot_table(index='Location', columns='Product', values='Evaluation', aggfunc='mean').reset_index().melt(id_vars='Location', var_name='Product', value_name='Mean Evaluation')
        create_and_save_plot(Products_Saudi_Arabia_T, 'Location', 'Mean Evaluation', 'Product', 'Evaluation by Product in Saudi Arabia', 'Location', 'Mean Evaluation', 'evaluation_by_product_in_saudi_arabia.png', images_dir, rotation=0)


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
            # أضف المدن الأخرى هنا
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

@app.get("/nivea", response_class=HTMLResponse)
async def read_nivea(request: Request):
    return templates.TemplateResponse("nivea.html", {"request": request})

@app.get("/nivea-analysis", response_class=JSONResponse)
async def nivea_analysis():
    try:
        df = pd.read_csv(r"C:\Users\HP\Desktop\Website\Data.csv")
        Products = df[['ID','age','Location','gender','social status','Product','Product Type','Evaluation','Product compliant']]
        Products['Product'] = Products['Product'].str.strip()
        Products_Nivea = Products[Products['Product'].str.contains('Nivea', case=False, na=False)]
        
        images_dir = r"C:\Users\HP\Desktop\Website\images"
        os.makedirs(images_dir, exist_ok=True)

        logger.info(f"Columns in Products_Nivea: {Products_Nivea.columns.tolist()}")

        Products_Nivea_Location = Products_Nivea.pivot_table(index='Product', columns='Location', values='Evaluation', aggfunc='mean').reset_index().melt(id_vars='Product', var_name='Location', value_name='Mean Evaluation')
        create_and_save_plot(Products_Nivea_Location, 'Location', 'Mean Evaluation', 'Product', 'Mean Evaluation of Nivea Products by Location', 'Location', 'Mean Evaluation', 'nivea_location.png', images_dir)
        logger.info("Created plot: nivea_location.png")

        Products_Nivea_gender = Products_Nivea.pivot_table(index='Product', columns='gender', values='Evaluation', aggfunc='mean').reset_index().melt(id_vars='Product', var_name='Gender', value_name='Mean Evaluation')
        create_and_save_plot(Products_Nivea_gender, 'Mean Evaluation', 'Product', 'Gender', 'Mean Evaluation of Nivea Products by Gender', 'Mean Evaluation', 'Product', 'nivea_gender.png', images_dir, orient='h')
        logger.info("Created plot: nivea_gender.png")

        Products_Nivea_Type = Products_Nivea.pivot_table(index='Product', columns='Product Type', values='Evaluation', aggfunc='mean').reset_index().melt(id_vars='Product', var_name='Product Type', value_name='Mean Evaluation')
        create_and_save_plot(Products_Nivea_Type, 'Mean Evaluation', 'Product', 'Product Type', 'Mean Evaluation of Nivea Products by Product Type', 'Mean Evaluation', 'Product', 'nivea_type.png', images_dir, orient='h')
        logger.info("Created plot: nivea_type.png")

        Products_Nivea_age = Products_Nivea.pivot_table(index='Product', columns='age', values='Evaluation', aggfunc='mean').reset_index().melt(id_vars='Product', var_name='Age Group', value_name='Mean Evaluation')
        create_and_save_plot(Products_Nivea_age, 'Age Group', 'Mean Evaluation', 'Product', 'Mean Evaluation of Nivea Products by Age Group', 'Age Group', 'Mean Evaluation', 'nivea_age.png', images_dir)
        logger.info("Created plot: nivea_age.png")


        analysis_data = {
            "location": "nivea_location.png",
            "gender": "nivea_gender.png",
            "type": "nivea_type.png",
            "age": "nivea_age.png"
        }
        
        logger.info(f"Analysis data: {analysis_data}")
        return JSONResponse(content=analysis_data)
    except KeyError as e:
        logger.error(f"KeyError: {e}")
        return JSONResponse(content={"error": f"KeyError: {e}"}, status_code=500)
    except Exception as e:
        logger.error(f"Error processing analysis: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    age: int
    gender: str
    socialstatus: str
    location: str

@app.post("/users/")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = User(username=user.username, email=user.email, password=user.password, age=user.age, gender=user.gender, socialstatus=user.socialstatus, location=user.location)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

class ProductCreate(BaseModel): 
    name: str
    type: str
    image: str

@app.post("/products/")
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    db_product = Product(name=product.name, type=product.type, image=product.image)
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

class UserProductRatingCreate(BaseModel):
    user_id: int
    product_id: int
    rating: float

@app.post("/ratings/")
def create_rating(rating: UserProductRatingCreate, db: Session = Depends(get_db)):
    db_rating = UserProductRating(user_id=rating.user_id, product_id=rating.product_id, rating=rating.rating)
    db.add(db_rating)
    db.commit()
    db.refresh(db_rating)
    return db_rating

class UserLogin(BaseModel):
    email: str
    password: str

@app.post("/login")
def login(user: UserLogin, request: Request, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user and db_user.password == user.password:
        request.session['user'] = db_user.username
        return {"message": "Login successful"}

@app.get("/logout")
def logout(request: Request):
    request.session.pop('user', None)
    return RedirectResponse(url="/")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)