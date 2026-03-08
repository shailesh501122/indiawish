from fastapi import APIRouter, Depends, Form, UploadFile, File, HTTPException
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from ...db.session import get_db
from ...models.user import User
from ...models.marketplace import Listing, Property, Category
from ..deps import get_current_admin

router = APIRouter()

@router.get("/stats")
def get_admin_stats(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    user_count = db.query(User).count()
    listing_count = db.query(Listing).count()
    property_count = db.query(Property).count()
    
    # Category distribution for listings
    category_stats = db.query(
        Category.name, 
        func.count(Listing.id).label("count")
    ).join(Listing, Category.id == Listing.category_id, isouter=True).group_by(Category.name).all()
    
    category_data = [{"name": name or "Uncategorized", "count": count} for name, count in category_stats]
    
    # Simple revenue simulation based on active listings/properties (dummy for now but linked to data)
    # Total "value" in the system
    total_listing_value = db.query(func.sum(Listing.price)).scalar() or 0
    total_property_value = db.query(func.sum(Property.price)).scalar() or 0
    
    return {
        "users": user_count,
        "listings": listing_count,
        "properties": property_count,
        "totalValue": total_listing_value + total_property_value,
        "categoryData": category_data,
        "recentUsers": user_count, # Just counts for now
        "revenueGrowth": "+12.5%", # Hardcoded trend
    }

@router.get("/users")
def get_all_users(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    users = db.query(User).all()
    return [{
        "id": u.id,
        "email": u.email,
        "firstName": u.first_name,
        "lastName": u.last_name,
        "roles": u.roles.split(","),
        "createdAt": u.created_at,
        "isActive": u.is_active
    } for u in users]

@router.get("/listings")
def get_all_listings(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    listings = db.query(Listing).all()
    return listings

@router.get("/properties")
def get_all_properties(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    properties = db.query(Property).all()
    return properties

# Category Management
from ...schemas.marketplace import CategoryRead
from fastapi import Form, UploadFile, File, HTTPException
import os
import shutil
import uuid

# Construct the path to local uploads
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "..", "uploads")

async def save_upload_file(file: UploadFile) -> str:
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image.")
    
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return f"/uploads/{unique_filename}"

@router.post("/categories", response_model=CategoryRead)
async def create_category(
    name: str = Form(...),
    description: str = Form(None),
    icon_file: UploadFile = File(None),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    icon_path = None
    if icon_file:
        icon_path = await save_upload_file(icon_file)
    
    new_cat = Category(
        name=name,
        description=description,
        icon=icon_path
    )
    db.add(new_cat)
    db.commit()
    db.refresh(new_cat)
    return new_cat

@router.put("/categories/{category_id}", response_model=CategoryRead)
async def update_category(
    category_id: str,
    name: str = Form(None),
    description: str = Form(None),
    icon_file: UploadFile = File(None),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    cat = db.query(Category).filter(Category.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    
    if name is not None:
        cat.name = name
    if description is not None:
        cat.description = description
    
    if icon_file:
        cat.icon = await save_upload_file(icon_file)
    
    db.commit()
    db.refresh(cat)
    return cat

@router.delete("/categories/{category_id}")
def delete_category(
    category_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    cat = db.query(Category).filter(Category.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    
    db.delete(cat)
    db.commit()
    return {"message": "Category deleted"}

# Subcategory Management
from ...models.marketplace import SubCategory
from ...schemas.marketplace import SubCategoryRead, SubCategoryCreate, SubCategoryUpdate
from fastapi import File, UploadFile
import os
import shutil

@router.get("/subcategories", response_model=List[SubCategoryRead])
def get_all_subcategories(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    return db.query(SubCategory).all()

@router.post("/subcategories", response_model=SubCategoryRead)
def create_subcategory(
    name: str = Form(...),
    category_id: str = Form(...),
    active_status: bool = Form(True),
    icon_file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    icon_path = None
    if icon_file:
        os.makedirs("static/icons", exist_ok=True)
        file_extension = os.path.splitext(icon_file.filename)[1]
        file_name = f"subcat_{uuid.uuid4()}{file_extension}"
        icon_path = f"static/icons/{file_name}"
        with open(icon_path, "wb") as buffer:
            shutil.copyfileobj(icon_file.file, buffer)

    new_sub = SubCategory(
        name=name,
        category_id=category_id,
        active_status=active_status,
        icon=icon_path
    )
    db.add(new_sub)
    db.commit()
    db.refresh(new_sub)
    return new_sub

@router.put("/subcategories/{subcategory_id}", response_model=SubCategoryRead)
def update_subcategory(
    subcategory_id: str,
    name: Optional[str] = Form(None),
    active_status: Optional[bool] = Form(None),
    icon_file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    sub = db.query(SubCategory).filter(SubCategory.id == subcategory_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subcategory not found")
    
    if name is not None:
        sub.name = name
    if active_status is not None:
        sub.active_status = active_status
    
    if icon_file:
        os.makedirs("static/icons", exist_ok=True)
        file_extension = os.path.splitext(icon_file.filename)[1]
        file_name = f"subcat_{uuid.uuid4()}{file_extension}"
        icon_path = f"static/icons/{file_name}"
        with open(icon_path, "wb") as buffer:
            shutil.copyfileobj(icon_file.file, buffer)
        sub.icon = icon_path
        
    db.commit()
    db.refresh(sub)
    return sub

@router.delete("/subcategories/{subcategory_id}")
def delete_subcategory(
    subcategory_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    sub = db.query(SubCategory).filter(SubCategory.id == subcategory_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subcategory not found")
    
    db.delete(sub)
    db.commit()
    return {"message": "Subcategory deleted"}

# Listing Management
from ...schemas.marketplace import ListingRead

@router.post("/listings", response_model=ListingRead)
async def create_listing(
    title: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    category_id: str = Form(...),
    subcategory_id: str = Form(None),
    location: str = Form(None),
    status: str = Form("Active"),
    images_files: List[UploadFile] = File(None),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    image_paths = []
    if images_files:
        for file in images_files:
            path = await save_upload_file(file)
            image_paths.append(path)
    
    new_listing = Listing(
        title=title,
        description=description,
        price=price,
        category_id=category_id,
        subcategory_id=subcategory_id,
        location=location,
        status=status,
        images=image_paths,
        user_id=admin.id # Admin is the owner for now if created via admin
    )
    db.add(new_listing)
    db.commit()
    db.refresh(new_listing)
    return new_listing

@router.put("/listings/{listing_id}", response_model=ListingRead)
async def update_listing(
    listing_id: str,
    title: str = Form(None),
    description: str = Form(None),
    price: float = Form(None),
    category_id: str = Form(None),
    subcategory_id: str = Form(None),
    location: str = Form(None),
    status: str = Form(None),
    images_files: List[UploadFile] = File(None),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    if title: listing.title = title
    if description: listing.description = description
    if price is not None: listing.price = price
    if category_id: listing.category_id = category_id
    if subcategory_id: listing.subcategory_id = subcategory_id
    if location: listing.location = location
    if status: listing.status = status
    
    if images_files:
        image_paths = []
        for file in images_files:
            path = await save_upload_file(file)
            image_paths.append(path)
        listing.images = image_paths # Replace images for now
        
    db.commit()
    db.refresh(listing)
    return listing

@router.delete("/listings/{listing_id}")
def delete_listing(
    listing_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    db.delete(listing)
    db.commit()
    return {"message": "Listing deleted"}

# Property Management
from ...schemas.marketplace import PropertyRead

@router.post("/properties", response_model=PropertyRead)
async def create_property(
    title: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    type: str = Form(...),
    address: str = Form(None),
    city: str = Form(None),
    area: float = Form(None),
    bedrooms: int = Form(None),
    bathrooms: int = Form(None),
    status: str = Form("Active"),
    images_files: List[UploadFile] = File(None),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    image_paths = []
    if images_files:
        for file in images_files:
            path = await save_upload_file(file)
            image_paths.append(path)
            
    new_prop = Property(
        title=title,
        description=description,
        price=price,
        type=type,
        address=address,
        city=city,
        area=area,
        bedrooms=bedrooms,
        bathrooms=bathrooms,
        status=status,
        images=image_paths,
        user_id=admin.id
    )
    db.add(new_prop)
    db.commit()
    db.refresh(new_prop)
    return new_prop

@router.put("/properties/{property_id}", response_model=PropertyRead)
async def update_property(
    property_id: str,
    title: str = Form(None),
    description: str = Form(None),
    price: float = Form(None),
    type: str = Form(None),
    address: str = Form(None),
    city: str = Form(None),
    area: float = Form(None),
    bedrooms: int = Form(None),
    bathrooms: int = Form(None),
    status: str = Form(None),
    images_files: List[UploadFile] = File(None),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    
    if title: prop.title = title
    if description: prop.description = description
    if price is not None: prop.price = price
    if type: prop.type = type
    if address: prop.address = address
    if city: prop.city = city
    if area is not None: prop.area = area
    if bedrooms is not None: prop.bedrooms = bedrooms
    if bathrooms is not None: prop.bathrooms = bathrooms
    if status: prop.status = status
    
    if images_files:
        image_paths = []
        for file in images_files:
            path = await save_upload_file(file)
            image_paths.append(path)
        prop.images = image_paths
        
    db.commit()
    db.refresh(prop)
    return prop

@router.delete("/properties/{property_id}")
def delete_property(
    property_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    
    db.delete(prop)
    db.commit()
    return {"message": "Property deleted"}
# Service Category Management
from ...models.services import ServiceCategory
from ...schemas.services import ServiceCategoryRead, ServiceCategoryUpdate

@router.get("/service-categories", response_model=List[ServiceCategoryRead])
def get_admin_service_categories(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    return db.query(ServiceCategory).all()

@router.post("/service-categories", response_model=ServiceCategoryRead)
async def create_service_category(
    name: str = Form(...),
    description: str = Form(None),
    icon_file: UploadFile = File(None),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    icon_path = None
    if icon_file:
        icon_path = await save_upload_file(icon_file)
    
    new_cat = ServiceCategory(
        name=name,
        description=description,
        icon=icon_path
    )
    db.add(new_cat)
    db.commit()
    db.refresh(new_cat)
    return new_cat

@router.put("/service-categories/{category_id}", response_model=ServiceCategoryRead)
async def update_service_category(
    category_id: str,
    name: str = Form(None),
    description: str = Form(None),
    icon_file: UploadFile = File(None),
    active_status: bool = Form(None),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    cat = db.query(ServiceCategory).filter(ServiceCategory.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Service Category not found")
    
    if name is not None:
        cat.name = name
    if description is not None:
        cat.description = description
    if active_status is not None:
        cat.active_status = active_status
    
    if icon_file:
        cat.icon = await save_upload_file(icon_file)
    
    db.commit()
    db.refresh(cat)
    return cat

@router.delete("/service-categories/{category_id}")
def delete_service_category(
    category_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    cat = db.query(ServiceCategory).filter(ServiceCategory.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Service Category not found")
    
    db.delete(cat)
    db.commit()
    return {"message": "Service Category deleted"}
