from fastapi import APIRouter, HTTPException, Depends, status,File, UploadFile
from pathlib import Path
from database import get_db
from auth.utils import hash_password, verify_password, verify_access_token, create_access_token, authenticate_user, role_required, get_current_user
from auth.schemas import *
from sqlalchemy.orm import Session, load_only
from models import *
from fastapi.security import OAuth2PasswordRequestForm
# from jose import JWTError, jwt
from pydantic import BaseModel
from datetime import datetime, timedelta
# from database import SessionLocal, engine
from sqlalchemy.sql.expression import select
from typing import Optional, Annotated, List
from config import settings
from sqlalchemy.orm import joinedload

router = APIRouter()
user_dependency = Annotated[Session, Depends(get_current_user)]

# Define a Pydantic model for the login request body
class LoginRequest(BaseModel):
    username: str
    password: str
# Login route
@router.post("/login")
def login_user(login_data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == login_data.username).first()

    if user is None or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    access_token = create_access_token(data={"id": user.id, "sub": user.username, "role": user.role, 
    })

    # Return the id along with the access_token and role
    return {
        "id": user.id,
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role
    }

@router.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):    
    
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=60)
    access_token = create_access_token(
        data={"sub": user.username, "id": user.id, "role": user.role}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/verify-token/{token}")
async def verify_user_token(token: str):
    verify_access_token(token=token)
    return {"message": "Token is valid"}

# check if a username is already taken
@router.get("/check-username/{username}")
def check_username(username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if user:
        return {"is_taken": True}
    return {"is_taken": False}

# create user endpoint
@router.post("/register")
def register_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    ):
    # Check if username already exists
    existing_user = db.query(User).filter(User.username == user.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists! Choose another one.")

    # Hash the user's password
    hashed_password = hash_password(user.password)

    try:
        # Try to Create and save the user
        new_user = User(**user.dict(), password_hash=hashed_password)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except Exception as e:
        if 'unique constraint' in str(e):
            raise HTTPException(status_code=400, detail="Username already exists")
        else:
            raise # Re-raise the original exception
    # return {"message": "User registered successfully", "user_id": new_user.id}
    return user

# get all user
@router.get("/users") # add role based dependency later
def get_all_users(db: Session = Depends(get_db)):
    user_data = db.query(User).options(load_only(User.id, User.username, User.role)).all()
    return user_data

# getting all-users and their specific infos
@router.get("/admin/all-users") # add role based dependency later
def get_all_users(db: Session = Depends(get_db)):
    # returing a list of users with their details
    users = db.query(User).options(load_only(User.id, User.username, User.role)).all()
    admin_users = db.query(User).filter(User.role == "admin").all()
    # users_details = []
    users_details = [admin for admin in admin_users] # including admin info
    for user in users:
        if user.role == "client":
            details = db.query(Client).filter(Client.user_id == user.id).first()
            # adding information seperately for now, because the table have difference in column naming
            name = (details.given_name + " " if details.given_name else "") + (details.surname + " " if details.surname else "") # sending given name + surname  

            company = db.query(Company).filter(Company.id == details.company_id).first()

            user_details = ReadUserDetails(
                id = user.id,
                username = user.username,
                role = user.role,
                name = name,
                email = details.home_email,
                mobile = details.home_mobile,
                company_name = company.name,
            )
            users_details.append(user_details)
            
        if user.role == "staff":
            details = db.query(Staff).filter(Staff.user_id == user.id).first()
            # title = details.title
            # given_name = details.given_name            
            # surname = details.surname
            # preferred_name = details.preferred_name
            # joining the name with null handling
            name = (details.given_name + " " if details.given_name else "") + (details.surname + " " if details.surname else "") # sending given name + surname  

            company = db.query(Company).filter(Company.id == details.company_id).first()
        
            user_details = ReadUserDetails(
                id = user.id,
                username = user.username,
                role = user.role,
                name = name,
                email = details.home_email,
                mobile = details.home_mobile,
                company_name = company.name,
            )
            users_details.append(user_details)   
    return users_details

# get user by user_id
@router.get("/users/{user_id}")
def get_user_by_id(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).options(load_only(User.id, User.username, User.role)).first()
    return user if user else {"message": "No user found!"}

# get user by username
@router.get("/users-username/{username}")
def get_user_by_username(username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).options(load_only(User.id, User.username, User.role)).first()
    return user

# update user by user_id
@router.put("/user/{userId}")
def update_user(userId: int, user_update: UserUpdate, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.id == userId).first()
    
    if user is None:
        raise HTTPException(status_code=404, detail="User not found!")
    
    existing_user = db.query(User).filter(User.username == user_update.username).first()
    if existing_user and existing_user.id != user.id:
        raise HTTPException(status_code=400, detail="This Username is already exists!")
    
    if user_update.username:
        user.username = user_update.username
    if user_update.role:
        user.role = user_update.role
    
    db.commit()
    db.refresh(user)
    
    return {"message": "User updated successfully", "user": user}

# delete user by userId
@router.delete("/users/{userId}")
def delete_user(userId: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == userId).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    if user.role == "client":
        ob_client = db.query(Client).filter(Client.user_id == userId).first()
        if ob_client:
            # Delete all tasks associated with this client
            db.query(Task).filter(Task.client_id == ob_client.id).delete()
            db.commit()
            # Now delete the client record
            db.delete(ob_client)
            db.commit()

    # Manually delete associated staffs and their tasks
    if user.role == "staff":
        ob_staff = db.query(Staff).filter(Staff.user_id == userId).first()
        if ob_staff:
            # Delete all tasks associated with this staff
            db.query(Task).filter(Task.staff_id == ob_staff.id).delete()
            db.commit()
            db.delete(ob_staff)
            db.commit()

    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully", "user": user}

# get current user
@router.get("/users/me")
async def get_current_user_info(
    current_user: UserRead = Depends(get_current_user),
    # current_user: user_dependency,
    # db: Session = Depends(get_db)
    ):
    return current_user

# creating client
@router.post("/register-participant/{userId}")
def register_client(
    userId: int, 
    client: ClientCreate, 
    db: Session = Depends(get_db)
    ):
    # Ensure the user_id exists and is of role 'client'
    user = db.query(User).filter(User.id == userId).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found!")
    
    existing_client = db.query(Client).filter(Client.user_id == userId).first()
    if existing_client:
        raise HTTPException(status_code=400, detail="User is already registered as a Participant!")
    
    existing_ndis = db.query(Client).filter(Client.ndi == client.ndi).first()
    if existing_ndis:
        raise HTTPException(status_code=400, detail="A Participant with this Ndis already exists!")
    
    if user.role != "client":
        raise HTTPException(status_code=400, detail="User is not a client! This is only for client registration.")
    
    company = db.query(Company).filter(Company.id == client.company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company does not exist! Check the company ID.")
    # If company information is needed

    file_path = None
    # Process the base64 image
    if client.image:
        image_data_bytes = base64.b64decode(client.image.split(",")[1])
        upload_dir = Path("uploads/profile_pics/") / str(userId)
        upload_dir.mkdir(parents=True, exist_ok=True)
        file_path = upload_dir / f"{userId}.jpg"
        with open(f"{upload_dir}/{userId}.jpg", "wb") as image_file:
            image_file.write(image_data_bytes)
    
    # Create the client
    db_client = Client(
        user_id=userId,
        disability=client.disability,
        ndi=client.ndi,
        company_id=client.company_id,
        reference=client.reference,
        image_path=str(file_path),
        # New fields for additional information
        date_of_reg=client.date_of_reg,
        plan_start_date = client.plan_start_date,
        plan_end_date = client.plan_end_date,

        surname=client.surname,
        given_name=client.given_name,
        sex=client.sex,
        aboriginal=client.aboriginal,
        preferred_name=client.preferred_name,
        date_of_birth=client.date_of_birth,
        residence_street=client.residence_street,
        residence_state=client.residence_state,
        residence_postcode=client.residence_postcode,
        postal_street=client.postal_street,
        postal_state=client.postal_state,
        postal_postcode=client.postal_postcode,
        home_mobile=client.home_mobile, # renamed mobile_phone to home_mobile in model, db and shcema
        home_phone=client.home_phone,
        home_email=client.home_email, # renamed email to home_email in model, db and schema
        ndis_start_date=client.ndis_start_date,
        ndis_end_date=client.ndis_end_date,
        ndis_plan_review_date=client.ndis_plan_review_date, # added ndis_plan_review_date in model, db and schema
        funding_type=client.funding_type,
        plan_provider_name=client.plan_provider_name,
        plan_provider_email=client.plan_provider_email,
        plan_provider_phone=client.plan_provider_phone,
        registered_other_ndis=client.registered_other_ndis,
        service_received_other_ndis=client.service_received_other_ndis,
        adv_surname=client.adv_surname,
        adv_given_name=client.adv_given_name,
        adv_relationship=client.adv_relationship,
        adv_phone=client.adv_phone,
        adv_mobile=client.adv_mobile,
        adv_email=client.adv_email,
        adv_address=client.adv_address,
        adv_postal_address=client.adv_postal_address,
        birth_country=client.birth_country,
        main_language=client.main_language,
        lang_interpreter_required=client.lang_interpreter_required,
        cultural_bariers=client.cultural_bariers,

        verbal_communication=client.verbal_communication, # added verbal_communication in model, db, schema and route
        interpreter_needed=client.interpreter_needed, # added interpreter_needed in model, db, schema and route
        interpreter_language=client.interpreter_language, # added interpreter_language in model, db, schema and route

        cultural_values=client.cultural_values,
        cultural_behaviours=client.cultural_behaviours,
        communication_literacy=client.communication_literacy,
        weight=client.weight,
        height=client.height,
        eye_color=client.eye_color,
        complexion=client.complexion,
        build=client.build,
        hair_color=client.hair_color,
        facial_hair=client.facial_hair,
        birth_marks=client.birth_marks,
        tattos=client.tattos,
        emergency1_name=client.emergency1_name,
        emergency1_relationship=client.emergency1_relationship,
        emergency1_mobile=client.emergency1_mobile,
        emergency1_phone=client.emergency1_phone,
        emergency2_name=client.emergency2_name,
        emergency2_relationship=client.emergency2_relationship,
        emergency2_mobile=client.emergency2_mobile,
        emergency2_phone=client.emergency2_phone,
        gp_clinic_name=client.gp_clinic_name,
        gp_firstname=client.gp_firstname,
        gp_surname=client.gp_surname,
        gp_email=client.gp_email,
        gp_address=client.gp_address,
        gp_phone=client.gp_phone,
        gp_mobile=client.gp_mobile,
        support_contact_name=client.support_contact_name,
        support_relationship=client.support_relationship,
        support_mobile=client.support_mobile,
        support_phone=client.support_phone,
        have_specialist=client.have_specialist,
        specialist_clinic_name=client.specialist_clinic_name,
        specialist_email=client.specialist_email,
        specialist_firstname=client.specialist_firstname,
        specialist_surname=client.specialist_surname,
        specialist_address=client.specialist_address,
        specialist_mobile=client.specialist_mobile,
        specialist_phone=client.specialist_phone,
        living_arrangement=client.living_arrangement,
        travel=client.travel,
        important_people=client.important_people, # added important_people in model, db, schema and route
    )

    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    return db_client

# get all clients staff-company specific
@router.get("/staff/all-participants")
def get_all_clients_staff(
    current_user: user_dependency, 
    db: Session = Depends(get_db)
    ):
    
    staff = db.query(Staff).filter(Staff.user_id == current_user.id).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found!")
    
    clients = db.query(Client).filter(Client.company_id == staff.company_id).all()
    clients_details = []
    # user_details = ReadUserDetails()
    for client in clients:
        given_name = client.given_name            
        surname = client.surname
        # joining the name
        name = (given_name + " " if given_name else "") + (surname + " " if surname else "")
        email = client.home_email
        mobile = client.home_mobile

        # company = db.query(Company).filter(Company.id == client.company_id).first()
        # company_name = company.name

        client_user = db.query(User).filter(User.id == client.user_id).first()
        
        client_details = ReadClientInfo(
            id = client.id,
            user_id = client.user_id,
            username = client_user.username,
            name = name,
            email = email,
            mobile = mobile,
        )
        clients_details.append(client_details)        
    return clients_details

from dataclasses import asdict
# get client details by userId
@router.get("/participant/{userId}")
def get_client_details(userId: int, db: Session = Depends(get_db)):
    client = db.query(Client).filter(Client.user_id == userId).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found!")
    
    user = db.query(User).filter(User.id == userId).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found!")

    # return client
    return ReadClientDetails.from_orm(client)
    # return ReadClientDetails(
    #     user_id=userId,
    #     disability=client.disability,
    #     ndi=client.ndi,
    #     company_id=client.company_id,
    #     reference=client.reference,
    #     image=client.image_path,
    #     # New fields for additional information
    #     date_of_reg=client.date_of_reg,
    #     plan_start_date = client.plan_start_date,
    #     plan_end_date = client.plan_end_date,

    #     surname=client.surname,
    #     given_name=client.given_name,
    #     sex=client.sex,
    #     aboriginal=client.aboriginal,
    #     preferred_name=client.preferred_name,
    #     date_of_birth=client.date_of_birth,
    #     residence_street=client.residence_street,
    #     residence_state=client.residence_state,
    #     residence_postcode=client.residence_postcode,
    #     postal_street=client.postal_street,
    #     postal_state=client.postal_state,
    #     postal_postcode=client.postal_postcode,
    #     home_mobile=client.home_mobile, # renamed mobile_phone to home_mobile in model, db and shcema
    #     home_phone=client.home_phone,
    #     home_email=client.home_email, # renamed email to home_email in model, db and schema
    #     ndis_start_date=client.ndis_start_date,
    #     ndis_end_date=client.ndis_end_date,
    #     ndis_plan_review_date=client.ndis_plan_review_date, # added ndis_plan_review_date in model, db and schema
    #     funding_type=client.funding_type,
    #     plan_provider_name=client.plan_provider_name,
    #     plan_provider_email=client.plan_provider_email,
    #     plan_provider_phone=client.plan_provider_phone,
    #     registered_other_ndis=client.registered_other_ndis,
    #     service_received_other_ndis=client.service_received_other_ndis,
    #     adv_surname=client.adv_surname,
    #     adv_given_name=client.adv_given_name,
    #     adv_relationship=client.adv_relationship,
    #     adv_phone=client.adv_phone,
    #     adv_mobile=client.adv_mobile,
    #     adv_email=client.adv_email,
    #     adv_address=client.adv_address,
    #     adv_postal_address=client.adv_postal_address,
    #     birth_country=client.birth_country,
    #     main_language=client.main_language,
    #     lang_interpreter_required=client.lang_interpreter_required,
    #     cultural_bariers=client.cultural_bariers,

    #     verbal_communication=client.verbal_communication, # added verbal_communication in model, db, schema and route
    #     interpreter_needed=client.interpreter_needed, # added interpreter_needed in model, db, schema and route
    #     interpreter_language=client.interpreter_language, # added interpreter_language in model, db, schema and route

    #     cultural_values=client.cultural_values,
    #     cultural_behaviours=client.cultural_behaviours,
    #     communication_literacy=client.communication_literacy,
    #     weight=client.weight,
    #     height=client.height,
    #     eye_color=client.eye_color,
    #     complexion=client.complexion,
    #     build=client.build,
    #     hair_color=client.hair_color,
    #     facial_hair=client.facial_hair,
    #     birth_marks=client.birth_marks,
    #     tattos=client.tattos,
    #     emergency1_name=client.emergency1_name,
    #     emergency1_relationship=client.emergency1_relationship,
    #     emergency1_mobile=client.emergency1_mobile,
    #     emergency1_phone=client.emergency1_phone,
    #     emergency2_name=client.emergency2_name,
    #     emergency2_relationship=client.emergency2_relationship,
    #     emergency2_mobile=client.emergency2_mobile,
    #     emergency2_phone=client.emergency2_phone,
    #     gp_clinic_name=client.gp_clinic_name,
    #     gp_firstname=client.gp_firstname,
    #     gp_surname=client.gp_surname,
    #     gp_email=client.gp_email,
    #     gp_address=client.gp_address,
    #     gp_phone=client.gp_phone,
    #     gp_mobile=client.gp_mobile,
    #     support_contact_name=client.support_contact_name,
    #     support_relationship=client.support_relationship,
    #     support_mobile=client.support_mobile,
    #     support_phone=client.support_phone,
    #     have_specialist=client.have_specialist,
    #     specialist_clinic_name=client.specialist_clinic_name,
    #     specialist_email=client.specialist_email,
    #     specialist_firstname=client.specialist_firstname,
    #     specialist_surname=client.specialist_surname,
    #     specialist_address=client.specialist_address,
    #     specialist_mobile=client.specialist_mobile,
    #     specialist_phone=client.specialist_phone,
    #     living_arrangement=client.living_arrangement,
    #     travel=client.travel,
    #     important_people=client.important_people, # added important_people in model, db, schema and route
    # )

# get client details by client_id
@router.get("/participant/{clientId}/participantId")
def get_client_details(clientId: int,
                       current_user: user_dependency,
                        db: Session = Depends(get_db)
                        ):
    client = db.query(Client).filter(Client.id == clientId).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found!")
    return client

# update clients details
@router.put("/participant/{userId}")
def update_client(userId: int, client_update: ClientUpdate, db: Session = Depends(get_db)):
    # Find the user by username
    db_user = db.query(User).filter(User.id == userId).first()
    
    if not db_user:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Find the client by user_id (username)
    db_client = db.query(Client).filter(Client.user_id == userId).first()
    
    if not db_client:
        raise HTTPException(status_code=404, detail="Client details not found")

    # Check and retrieve the company if provided
    if client_update.company_id is not None:
        company = db.query(Company).filter(Company.id == client_update.company_id).first()
        if not company:
            raise HTTPException(status_code=404, detail="Company does not exist! Check the company ID.")
        db_client.company_id = client_update.company_id
    
    # exist_ndi = db.query(Client).filter(Client.ndi == client_update.ndi).first()
    # if exist_ndi:
    #     raise HTTPException(status_code=400, detail="Client with the same ndi already exists!")

    # Update all the fields if provided in the request
    for key, value in client_update.dict(exclude_unset=True).items():
        setattr(db_client, key, value)
    
    db.commit()
    db.refresh(db_client)
    
    return db_client

# delete participant by userId
@router.delete("/staff/participant/{userId}/delete")
def delete_participant(userId: int, current_user: user_dependency, db: Session = Depends(get_db)):

    if current_user.role != UserRole.staff:
        raise HTTPException(status_code=403, detail="Not authorized to perform this action!")
    db_user = db.query(User).filter(User.id == userId).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found!")
    ob_client = db.query(Client).filter(Client.user_id == userId).first()
    if ob_client:
        # Delete all tasks associated with this client
        db.query(Task).filter(Task.client_id == ob_client.id).delete()
        db.commit()
        # Now delete the client record
        db.delete(ob_client)
        db.commit()
    db.delete(db_user)
    db.commit()
    return {"detail": "User deleted successfully", 
            "participant": db_user}

# # register staff endpoint
# @router.post("/register-staff/{userId}")
# async def register_staff(
#     userId: int,
#     staff: StaffCreate,
#     # image: Optional[UploadFile] = File(None),
#     db: Session = Depends(get_db),
#     ):
#     # Ensure the user exists and is of role 'staff'
#     user = db.query(User).filter(User.id == userId).first()
    
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found!")
    
#     if user.role != "staff":
#         raise HTTPException(status_code=400, detail="User is not a staff! This is only for staff registration.")
    
#     existing_staff = db.query(Staff).filter(Staff.user_id == userId).first()
#     if existing_staff:
#         raise HTTPException(status_code=400, detail="Staff already registered!")
    
#     # Ensure the company exists
#     company = db.query(Company).filter(Company.id == staff.company_id).first()
#     if not company:
#         raise HTTPException(status_code=404, detail="Company does not exist! Check the company name.")
    
#     # print(staff.dict())

#     file_path = None
#     if staff.image_path:
#         # Define the directory to save the files
#         print("MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM image")
#         upload_dir = Path("uploads/profile_pics/") / str(userId)
#         upload_dir.mkdir(parents=True, exist_ok=True)

#         file_path = upload_dir / staff.image_path.filename

#         with open(file_path, "wb") as buffer:
#             buffer.write(staff.image_path.file.read())

#     # if image_path:
#     #     # Define the directory to save the files
#     #     print("MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM image")
#     #     upload_dir = Path("uploads/profile_pics/") / str(userId)
#     #     upload_dir.mkdir(parents=True, exist_ok=True)

#     #     file_path = upload_dir / image_path.filename

#     #     with open(file_path, "wb") as buffer:
#     #         buffer.write(image_path.file.read())

#     # Create the staff
#     db_staff = Staff(
#         user_id=userId,
#         company_id=staff.company_id, # if company exists
#         date_of_reg=staff.date_of_reg, # added date_of_reg field from model, db, shcema and route
#         image_path = str(file_path) if file_path else None,
#         title=staff.title,
#         surname=staff.surname,
#         given_name=staff.given_name,
#         preferred_name=staff.preferred_name,
#         dob=staff.date_of_birth, # changed dob to date_of_birth in schema only
#         residence_street=staff.residence_street,
#         residence_state=staff.residence_state,
#         residence_postcode=staff.residence_postcode,
#         postal_street=staff.postal_street,
#         postal_state=staff.postal_state,
#         postal_postcode=staff.postal_postcode,
#         home_email=staff.home_email,
#         home_phone=staff.home_phone,
#         home_mobile=staff.home_mobile,
#         emergency1_name=staff.emergency1_name,
#         emergency1_relationship=staff.emergency1_relationship,
#         emergency1_mobile=staff.emergency1_mobile,
#         emergency1_phone=staff.emergency1_phone,
#         emergency2_name=staff.emergency2_name,
#         emergency2_relationship=staff.emergency2_relationship,
#         emergency2_mobile=staff.emergency2_mobile,
#         emergency2_phone=staff.emergency2_phone,
#         bank1_name=staff.bank1_name,
#         bank1_acc_name=staff.bank1_acc_name,
#         bank1_acc_no=staff.bank1_acc_no,
#         bank1_branch=staff.bank1_branch,
#         bank1_bsb=staff.bank1_bsb,
#         bank2_name=staff.bank2_name,
#         bank2_acc_name=staff.bank2_acc_name,
#         bank2_acc_no=staff.bank2_acc_no,
#         bank2_branch=staff.bank2_branch,
#         bank2_bsb=staff.bank2_bsb,
#         bank_unit=staff.bank_unit,
#         bank_amount=staff.bank_amount,
#         bank_percent_net_pay=staff.bank_percent_net_pay,
#         employee_tax=staff.employee_tax,
#         abn=staff.abn,
#         secondary_employment=staff.secondary_employment,
#         secondary_employment_details=staff.secondary_employment_details,
#         epilepsy=staff.epilepsy,
#         diabetes=staff.diabetes,
#         diabetes_type=staff.diabetes_type,
#         heart_condition=staff.heart_condition,
#         heart_condition_details=staff.heart_condition_details,
#         allergies=staff.allergies,
#         allergies_details=staff.allergies_details,
#         health_others=staff.health_others,
#         health_others_details=staff.health_others_details,
#         australian=staff.australian,
#         aus_permanent=staff.aus_permanent,
#         have_working_visa=staff.have_working_visa,
#         visa_expiary_date=staff.visa_expiary_date,
#         visa_restrictions=staff.visa_restrictions
#     )
#     print(db_staff)
#     db.add(db_staff)
#     db.commit()
#     db.refresh(db_staff)
#     return db_staff

# register staff endpoint

import base64
class ImageData(BaseModel):
    image: str
@router.post("/register-staff/{userId}")
async def register_staff(
    userId: int,
    staff: StaffCreate,
    db: Session = Depends(get_db),
    ):

    print("MMMMMMM Hit the route for registering staff, staffData: ", locals())
    # Ensure the user exists and is of role 'staff'
    user = db.query(User).filter(User.id == userId).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found!")
    
    if user.role != "staff":
        raise HTTPException(status_code=400, detail="User is not a staff! This is only for staff registration.")
    
    existing_staff = db.query(Staff).filter(Staff.user_id == userId).first()
    if existing_staff:
        raise HTTPException(status_code=400, detail="Staff already registered!")
    
    # Ensure the company exists
    company = db.query(Company).filter(Company.id == staff.company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company does not exist! Check the company name.")
    
    file_path = None
    # Process the base64 image
    if staff.image:
        image_data_bytes = base64.b64decode(staff.image.split(",")[1])
        upload_dir = Path("uploads/profile_pics/") / str(userId)
        upload_dir.mkdir(parents=True, exist_ok=True)
        file_path = upload_dir / f"{userId}.jpg"
        with open(f"{upload_dir}/{userId}.jpg", "wb") as image_file:
            image_file.write(image_data_bytes)

    # Create the staff
    db_staff = Staff(
        user_id=userId,
        company_id=staff.company_id, # if company exists
        date_of_reg=staff.date_of_reg, # added date_of_reg field from model, db, shcema and route
        image_path = file_path,
        title=staff.title,
        surname=staff.surname,
        given_name=staff.given_name,
        preferred_name=staff.preferred_name,
        dob=staff.date_of_birth, # changed dob to date_of_birth in schema only
        residence_street=staff.residence_street,
        residence_state=staff.residence_state,
        residence_postcode=staff.residence_postcode,
        postal_street=staff.postal_street,
        postal_state=staff.postal_state,
        postal_postcode=staff.postal_postcode,
        home_email=staff.home_email,
        home_phone=staff.home_phone,
        home_mobile=staff.home_mobile,
        emergency1_name=staff.emergency1_name,
        emergency1_relationship=staff.emergency1_relationship,
        emergency1_mobile=staff.emergency1_mobile,
        emergency1_phone=staff.emergency1_phone,
        emergency2_name=staff.emergency2_name,
        emergency2_relationship=staff.emergency2_relationship,
        emergency2_mobile=staff.emergency2_mobile,
        emergency2_phone=staff.emergency2_phone,
        bank1_name=staff.bank1_name,
        bank1_acc_name=staff.bank1_acc_name,
        bank1_acc_no=staff.bank1_acc_no,
        bank1_branch=staff.bank1_branch,
        bank1_bsb=staff.bank1_bsb,
        bank2_name=staff.bank2_name,
        bank2_acc_name=staff.bank2_acc_name,
        bank2_acc_no=staff.bank2_acc_no,
        bank2_branch=staff.bank2_branch,
        bank2_bsb=staff.bank2_bsb,
        bank_unit=staff.bank_unit,
        bank_amount=staff.bank_amount,
        bank_percent_net_pay=staff.bank_percent_net_pay,
        employee_tax=staff.employee_tax,
        abn=staff.abn,
        secondary_employment=staff.secondary_employment,
        secondary_employment_details=staff.secondary_employment_details,
        epilepsy=staff.epilepsy,
        diabetes=staff.diabetes,
        diabetes_type=staff.diabetes_type,
        heart_condition=staff.heart_condition,
        heart_condition_details=staff.heart_condition_details,
        allergies=staff.allergies,
        allergies_details=staff.allergies_details,
        health_others=staff.health_others,
        health_others_details=staff.health_others_details,
        australian=staff.australian,
        aus_permanent=staff.aus_permanent,
        have_working_visa=staff.have_working_visa,
        visa_expiary_date=staff.visa_expiary_date,
        visa_restrictions=staff.visa_restrictions
    )
    print(db_staff)
    db.add(db_staff)
    db.commit()
    db.refresh(db_staff)
    return db_staff

# get all staffs by company_id
@router.get("/admin/company/{companyId}/all-staffs")
def get_all_clients_staff(
    companyId: int,
    current_user: user_dependency, 
    db: Session = Depends(get_db)
    ):
    
    admin = db.query(User).filter(User.id == current_user.id).first()
    if not admin or (admin.role != 'admin'):
        raise HTTPException(status_code=400, detail="Not authorized to perform this action!")
    
    staffs = db.query(Staff).filter(Staff.company_id == companyId).all()
    staffs_details = []
    # user_details = ReadUserDetails()
    for staff in staffs:
        name = ""
        email = ""
        mobile = ""
        
        # title = staff.title # not sending title
        given_name = staff.given_name            
        surname = staff.surname
        # joining the name
        name = (given_name + " " if given_name else "") + (surname + " " if surname else "") # sending only given name and surname
        email = staff.home_email # renamed email to home_email in model, db and schema
        mobile = staff.home_mobile # renamed mobile_phone to mobile_phone in model, db and schema

        staff_user = db.query(User).filter(User.id == staff.user_id).first()
        
        staff_details = ReadStaffInfo(
            id = staff.id,
            username = staff_user.username,
            name = name,
            email = email,
            mobile = mobile,
        )
        staffs_details.append(staff_details)        
    return staffs_details

# get staff details by userId
@router.get("/user/staff/{userId}")
def get_staff_details(userId: int, db:Session = Depends(get_db)):
    
    staff = db.query(Staff).filter(Staff.user_id == userId).first()

    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found!")

    user = db.query(User).filter(User.id == userId).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return ReadStaffDetail(
        user_id=userId,
        staff_id=staff.id,
        username=user.username,
        role = user.role,
        name=staff.given_name or "Unknown",  # Handle possible None value
        image_path=staff.image_path,
        company_id=staff.company_id,
        title=staff.title,
        surname=staff.surname,
        given_name=staff.given_name,
        preferred_name=staff.preferred_name,
        date_of_birth=staff.dob, # changed dob to date_of_birth in model, db and schema
        residence_street=staff.residence_street,
        residence_state=staff.residence_state,
        residence_postcode=staff.residence_postcode,
        postal_street=staff.postal_street,
        postal_state=staff.postal_state,
        postal_postcode=staff.postal_postcode,
        home_email=staff.home_email,
        home_phone=staff.home_phone,
        home_mobile=staff.home_mobile,
        emergency1_name=staff.emergency1_name,
        emergency1_relationship=staff.emergency1_relationship,
        emergency1_mobile=staff.emergency1_mobile,
        emergency1_phone=staff.emergency1_phone,
        emergency2_name=staff.emergency2_name,
        emergency2_relationship=staff.emergency2_relationship,
        emergency2_mobile=staff.emergency2_mobile,
        emergency2_phone=staff.emergency2_phone,
        bank1_name=staff.bank1_name,
        bank1_acc_name=staff.bank1_acc_name,
        bank1_acc_no=staff.bank1_acc_no,
        bank1_branch=staff.bank1_branch,
        bank1_bsb=staff.bank1_bsb,
        bank2_name=staff.bank2_name,
        bank2_acc_name=staff.bank2_acc_name,
        bank2_acc_no=staff.bank2_acc_no,
        bank2_branch=staff.bank2_branch,
        bank2_bsb=staff.bank2_bsb,
        bank_unit=staff.bank_unit,
        bank_amount=staff.bank_amount,
        bank_percent_net_pay=staff.bank_percent_net_pay,
        employee_tax=staff.employee_tax,
        abn=staff.abn,
        secondary_employment=staff.secondary_employment,
        secondary_employment_details=staff.secondary_employment_details,
        epilepsy=staff.epilepsy,
        diabetes=staff.diabetes,
        diabetes_type=staff.diabetes_type,
        heart_condition=staff.heart_condition,
        heart_condition_details=staff.heart_condition_details,
        allergies=staff.allergies,
        allergies_details=staff.allergies_details,
        health_others=staff.health_others,
        health_others_details=staff.health_others_details,
        australian=staff.australian,
        aus_permanent=staff.aus_permanent,
        have_working_visa=staff.have_working_visa,
        visa_expiary_date=staff.visa_expiary_date,
        visa_restrictions=staff.visa_restrictions
    )

# updating staff info
@router.put("/update-staff/{userId}")
def update_staff(userId: int, staff_update: StaffUpdate, db: Session = Depends(get_db)):
    # Find the staff by staff_id
    db_staff = db.query(Staff).filter(Staff.user_id == userId).first()
    
    if not db_staff:
        raise HTTPException(status_code=404, detail="Staff not found!")
    
    # Update staff information
    for key, value in staff_update.dict(exclude_unset=True).items():
        setattr(db_staff, key, value)

    db.commit()
    db.refresh(db_staff)
    return db_staff

# getting all staff info
@router.get("/staffs/", response_model=List[StaffRead])
def get_all_staffs(db: Session = Depends(get_db)):
    staffs = db.query(Staff).all()
    return staffs

# getting staff details by staff_id
@router.get("/staff/{staffId}")
def get_staff_by_id(staffId: int, db: Session = Depends(get_db)):
    db_staff = db.query(Staff).filter(Staff.id == staffId).first()
    
    if not db_staff:
        raise HTTPException(status_code=404, detail="Staff not found!")
    
    return db_staff

# getting all staff by company name
@router.get("/staffs/company/{company_id}", response_model=List[StaffRead])
def get_staff_by_company_id(company_id: int, db: Session = Depends(get_db)):
    staffs = db.query(Staff).filter(Staff.company_id == company_id).all()
    
    if not staffs:
        raise HTTPException(status_code=404, detail="No staff found for the given company ID!")
    
    return staffs

# making task for a client by client_id
@router.post("/create-tasks/{participantId}", response_model=TaskRead)
def create_task(
    participantId: int,
    task: TaskCreate, 
    current_user: user_dependency,
    db: Session = Depends(get_db)
    ):

    if current_user.role != 'staff':
        raise HTTPException(status_code=403, detail="Not authorized")

    # Getting the staff
    staff = db.query(Staff).filter(Staff.user_id == current_user.id).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found!")
    # Getting the participant
    client = db.query(Client).filter(Client.id == participantId).first()
    if not client:
        raise HTTPException(status_code=404, detail="Participant not found!")
    
    start = datetime.combine(task.start_date, task.start_time)
    end = datetime.combine(task.end_date, task.end_time)

    # taskStart = datetime.combine(Task.start_date, Task.start_time)
    # taskEnd = datetime.combine(Task.end_date, Task.end_time)
    if end < start:
        raise HTTPException(status_code=404, detail="End time must be after start time!")
    
    # Check for time overlapping
    # overlapping_tasks = db.query(Task).filter(
    #     Task.staff_id == staff.id,
    #     Task.start_date <= task.end_date,
    #     Task.end_date >= task.start_date
    # ).all()
    overlapping_tasks = db.query(Task).filter(
        Task.staff_id == staff.id,
        Task.start_date <= task.end_date,
        Task.end_date >= task.start_date,
        Task.start_time <= task.end_time,
        Task.end_time >= task.start_time
    ).all()

    if overlapping_tasks:
        raise HTTPException(status_code=400, detail="Overlapping task found in the selected time!")
    
    new_task = Task(
        staff_id=staff.id,
        client_id=participantId,
        start_date=task.start_date, 
        start_time=task.start_time,
        end_date=task.end_date,
        end_time=task.end_time,
        service_type=task.service_type,
        tasks_list=task.tasks_list
    )
    
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task

# Get all tasks for admin
@router.get("/all-tasks", response_model=List[TaskReadDetails])
async def get_all_tasks(
    current_user: user_dependency,
    db: Session = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized! Only admin can access all tasks.")

    # Fetch all tasks with only the necessary fields for Staff and Client
    tasks = db.query(Task).options(
        joinedload(Task.staff).load_only(Staff.given_name, Staff.surname),  # Only load the necessary columns
        joinedload(Task.client).load_only(Client.given_name, Client.surname)  # Only load the necessary columns
    ).all()

    if not tasks:
        raise HTTPException(status_code=404, detail="No tasks found")

    task_data = [
        TaskReadDetails(
            id=task.id,
            staff_id=task.staff_id,
            staff_name=f"{task.staff.given_name} {task.staff.surname}" if task.staff else None,
            client_id=task.client_id,
            client_name=f"{task.client.given_name} {task.client.surname}" if task.client else None,
            start_date=task.start_date,
            start_time=task.start_time,
            end_date=task.end_date,
            end_time=task.end_time,
            hours=task.hours,
            service_type=task.service_type,
            tasks_list=task.tasks_list,
            done=task.done,
            done_time=task.done_time,
            approved=task.approved,
        ) for task in tasks
    ]

    return task_data

# get all staff specific tasks
@router.get("/tasks/staff/", response_model=List[TaskReadDetails])
def get_tasks_by_staff(
    current_user: user_dependency, 
    db: Session = Depends(get_db)
    ):

    staff = db.query(Staff).filter(Staff.user_id == current_user.id).first()
    staff_name = (staff.given_name + " " if staff.given_name else "") + (staff.surname + " " if staff.surname else "") # sending given name + surname

    tasks = db.query(Task).filter(Task.staff_id == staff.id).options(
        joinedload(Task.client).load_only(Client.given_name, Client.surname),  # Only load the necessary columns
        joinedload(Task.medias)  # Only load the necessary columns
    ).all()

    results = [
        TaskReadDetails(
            id=task.id,
            staff_id=task.staff_id,
            staff_name=staff_name,
            client_id=task.client_id,
            client_name=f"{task.client.given_name} {task.client.surname}" if task.client else None,
            start_date=task.start_date,
            start_time=task.start_time,
            end_date=task.end_date,
            end_time=task.end_time,
            hours=task.hours,
            service_type=task.service_type,
            tasks_list=task.tasks_list,
            done=task.done,
            done_time=task.done_time,
            approved=task.approved,
            media_files= [media.file_path for media in task.medias],
        )
            for task in tasks]

    return results

# may be can be deleted, will see later
# get all tasks by staff_id
@router.get("/tasks/staff/{staff_id}", response_model=List[TaskReadDetails])
def get_tasks_by_staff_id(
    staff_id: int,
    current_user: user_dependency,
    db: Session = Depends(get_db)):
    
    staff = db.query(Staff).filter(Staff.id == staff_id).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found!")
    
    if current_user.role != "admin" and current_user.id != staff.user_id:
        raise HTTPException(status_code=403, detail="You are not authorized to access this information!")

    tasks = db.query(Task).filter(Task.staff_id == staff.id).all()
    staff_name = (staff.given_name + " " if staff.given_name else "") + (staff.surname + " " if staff.surname else "") # sending given name + surname

    results = []
    for task in tasks:
        client_name=db.query(Client).filter(Client.id == task.client_id).first().preferred_name
        # fetching the media files
        media_files = db.query(Media).filter(Media.task_id == task.id).all()
        media_file_paths = [media.file_path for media in media_files]

        task_data = TaskReadDetails(
            id=task.id,
            staff_id=task.staff_id,
            staff_name=staff_name,
            client_id=task.client_id,
            client_name=client_name,
            start_date=task.start_date,
            start_time=task.start_time,
            end_date=task.end_date,
            end_time=task.end_time,
            hours=task.hours,
            service_type=task.service_type,
            tasks_list=task.tasks_list,
            done=task.done,
            done_time=task.done_time,
            approved=task.approved,
            media_files=media_file_paths
        )
        results.append(task_data)

    return results

# get all tasks by clientId
@router.get("/tasks/client/{clientId}", response_model=List[TaskReadDetails])
def get_tasks_by_staff(clientId: int, db: Session = Depends(get_db)):
    
    client = db.query(Client).filter(Client.id == clientId).first()
    client_name =(client.given_name + " " if client.given_name else "") + (client.surname + " " if client.surname else "") # sending given name + surname

    tasks = db.query(Task).filter(Task.client_id == clientId).all()
    if not tasks:
        raise HTTPException(status_code=404, detail="No tasks found for this client")

    results = []
    for task in tasks:
        staff = db.query(Staff).filter(Staff.id == task.staff_id).options(load_only(Staff.given_name, Staff.surname)).first() # optimized
        staff_name = (staff.given_name + " " if staff.given_name else "") + (staff.surname + " " if staff.surname else "") # sending given name + surname  
        media_files = db.query(Media).filter(Media.task_id == task.id).all()
        media_file_paths = [media.file_path for media in media_files]

        task_data = TaskReadDetails(
            id=task.id,
            staff_id=task.staff_id,
            staff_name=staff_name,
            client_id=task.client_id,
            client_name=client_name,
            start_date=task.start_date,
            start_time=task.start_time,
            end_date=task.end_date,
            end_time=task.end_time,
            hours=task.hours,
            service_type=task.service_type,
            tasks_list=task.tasks_list,
            done=task.done,
            done_time=task.done_time,
            approved=task.approved,
            media_files=media_file_paths
        )
        results.append(task_data)

    return results

# get a specific task by id
@router.get("/task/{task_id}")
def get_task_by_task_id(task_id: int, db: Session = Depends(get_db)): # will add user dependency later
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

# route for getting weekly tasks
# >>>>>> modified for the new db, working perfectly, usage not sure
# Calculate the start of the current week (e.g., Monday)
def get_current_week_start():
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())  # Monday as start of the week
    return start_of_week

# Get tasks for the current week
@router.get("/tasks/current-week", response_model=List[TaskReadDetails])
async def get_current_week_tasks( 
    current_user: user_dependency,
    db: Session = Depends(get_db),
    ):
    start_of_week = get_current_week_start()
    end_of_week = start_of_week + timedelta(days=6)
    print("MMMMMMMMMMMMMMMM: \n, start_of_week: ", start_of_week, "\n, end_of_week: ", end_of_week)
    if current_user.role == UserRole.staff.value:
        staff = db.query(Staff).filter(Staff.user_id == current_user.id).first()
        tasks = db.query(Task).filter(
            Task.staff_id == staff.id,
            Task.start_date >= start_of_week,
            Task.start_date <= end_of_week
        ).all()
    elif current_user.role == UserRole.client.value:
        client = db.query(Client).filter(Client.user_id == current_user.id).first()
        tasks = db.query(Task).filter(
            Task.client_id == client.id,
            Task.start_date >= start_of_week,
            Task.start_date <= end_of_week
        ).all()
    
    else:
        raise HTTPException(status_code=403, detail="Access forbidden!")
    results = []
    for task in tasks:
        staff = db.query(Staff).filter(Staff.id == task.staff_id).options(load_only(Staff.given_name, Staff.surname)).first() # optimized
        client = db.query(Client).filter(Client.id == task.client_id).options(load_only(Client.given_name, Client.surname)).first() # optimized
        staff_name = (staff.given_name + " " if staff.given_name else "") + (staff.surname + " " if staff.surname else "") # sending given name + surname
        client_name = (client.given_name + " " if client.given_name else "") + (client.surname + " " if client.surname else "") # sending given name + surname

        media_files = db.query(Media).filter(Media.task_id == task.id).all()
        media_file_paths = [media.file_path for media in media_files]

        task_data = TaskReadDetails(
            id=task.id,
            # timesheet_id=task.timesheet_id,
            staff_id=task.staff_id,
            staff_name=staff_name,
            client_id=task.client_id,
            client_name=client_name,
            start_date=task.start_date,
            start_time=task.start_time,
            end_date=task.end_date,
            end_time=task.end_time,
            hours=task.hours,
            service_type=task.service_type,
            tasks_list=task.tasks_list,
            done=task.done,
            done_time=task.done_time,
            approved=task.approved,
            media_files=media_file_paths
        )
        results.append(task_data)

    return results


# editing task
@router.put("/edit-task/{task_id}", response_model=TaskRead)
def edit_task(
    task_id: int,
    task_update: TaskCreate,
    current_user: user_dependency,
    db: Session = Depends(get_db)
):
    task_to_edit = db.query(Task).filter(Task.id == task_id).first()

    if not task_to_edit:
        raise HTTPException(status_code=404, detail="Task not found")

    staff = db.query(Staff).filter(Staff.user_id == current_user.id).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found!")
    
    print("MMMMMMM: \n staff.id: ", staff.id, "\n task_to_edit.staff_id: ", task_to_edit.staff_id)

    if task_to_edit.staff_id != staff.id:
        raise HTTPException(status_code=403, detail="Not authorized to edit this task")

    # Update the task fields if they are provided
    if task_update.start_date:
        task_to_edit.start_date = task_update.start_date
    if task_update.start_time:
        task_to_edit.start_time = task_update.start_time
    if task_update.end_date:
        task_to_edit.end_date = task_update.end_date
    if task_update.end_time:
        task_to_edit.end_time = task_update.end_time
    if task_update.service_type:
        task_to_edit.service_type = task_update.service_type

    # Update the tasks_list field if provided
    if task_update.tasks_list is not None:
        task_to_edit.tasks_list = task_update.tasks_list

    # Recalculate hours if any date/time was updated
    if any([task_update.start_date, task_update.start_time, task_update.end_date, task_update.end_time]):
        task_to_edit.hours = Task.calculate_hours(
            task_to_edit.start_date, task_to_edit.start_time,
            task_to_edit.end_date, task_to_edit.end_time
        )

    db.commit()
    db.refresh(task_to_edit)

    return task_to_edit


# Deleting task
@router.delete("/task/{task_id}/delete", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int, 
    current_user: user_dependency, 
    db: Session = Depends(get_db)
    ):
    # only admin and the tasks staff will be able to delete the task
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found!")

    staff = db.query(Staff).filter(Staff.user_id == current_user.id).first()

    # print("MMMMMMMMMMMMM: \n, staff or not: ", staff, not staff)

    # Check if user is allowed to delete the task
    if (current_user.role != "admin") and (not staff):
        raise HTTPException(status_code=403, detail="You are Not authorized to delete this task!")
    elif staff and (task.staff_id != staff.id):
        # print("MMMMMMMMMMMMM: \n, task.staff_id: ", task.staff_id)
        raise HTTPException(status_code=403, detail="You are Not authorized to delete other staffs task!")

    db.delete(task)
    db.commit()
    # print("MMMMMMMMMMMMM: \n, task deleted: ", task)

    # return None
    return {"message: ", "Task deleted successfully"}


# updating task status
@router.patch("/tasks/{task_id}/status")
async def update_task_status(
    task_id: int,
    status_upudate: TaskStatusUpdate,
    db: Session = Depends(get_db)
):
    print("MMMMMMMMMMMMM: \n, task_id, done:", task_id, status_upudate.done)
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task.done = status_upudate.done
    if status_upudate.done:
        task.done_time = datetime.utcnow()  # Store the current time if the task is marked as done
    else:
        task.done_time = None  # Clear done_time if the task is not done

    db.commit()
    db.refresh(task)
    
    # return task
    return {"message": "Task status updated successfully"}

# adding media
from fastapi.responses import FileResponse
@router.post("/tasks/{task_id}/upload-media", response_model=MediaRead)
async def upload_media(task_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Define the directory to save the files
    upload_dir = Path("uploads/") / str(task_id)
    upload_dir.mkdir(parents=True, exist_ok=True)

    file_path = upload_dir / file.filename

    with open(file_path, "wb") as buffer:
        buffer.write(file.file.read())

    # Save the file path in the Media table
    new_media = Media(task_id=task_id, file_path=str(file_path))
    db.add(new_media)
    db.commit()
    db.refresh(new_media)

    # return FileResponse(file_path) # used for debugging
    return new_media

# get media task specific
@router.get("/tasks/{task_id}/media", response_model=List[MediaRead])
async def get_media_for_task(task_id: int, db: Session = Depends(get_db)):
    media_list = db.query(Media).filter(Media.task_id == task_id).all()
    # if not media_list:
    #     raise HTTPException(status_code=404, detail="No media found for this task")
    return media_list

# delete media
@router.delete("/tasks/{media_id}/delete-media", response_model=dict)
async def delete_media(media_id: int, db: Session = Depends(get_db)):
    # Fetch the media record from the database
    media = db.query(Media).filter(Media.id == media_id).first()
    
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")

    # Convert the file path to a Path object
    file_path = Path(media.file_path)
    
    try:
        # Delete the file from the filesystem
        if file_path.exists():
            file_path.unlink()  # This deletes the file from the filesystem
        else:
            raise HTTPException(status_code=404, detail="File not found on disk")

        # Remove the record from the database
        db.delete(media)
        db.commit()
        
    except Exception as e:
        # Rollback the transaction in case of error
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting media: {str(e)}")

    return {"detail": "Media deleted successfully"}

from fastapi import Form, UploadFile, File

# Add a company with logo
@router.post("/register/company", response_model=CompanyOut)
async def add_company(
    current_user: user_dependency,
    db: Session = Depends(get_db),
    name: str = Form(...),
    abn: str = Form(...),
    web: str = Form(None),
    phone: str = Form(None),
    email: str = Form(None),
    address: str = Form(None),
    logo: UploadFile = File(None),  # Logo upload is optional
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized! Only Admin can See this.")
    
    db_company = db.query(Company).filter((Company.name == name) | (Company.abn == abn)).first()
    if db_company:
        raise HTTPException(status_code=400, detail="Company with this name or ABN already exists")
    
    new_company = Company(name=name, abn=abn, web=web, phone=phone, email=email, address=address)
    
    # Save the logo if uploaded
    if logo:
        logo_dir = Path("uploads/logos/") / name
        logo_dir.mkdir(parents=True, exist_ok=True)
        logo_path = logo_dir / logo.filename

        with open(logo_path, "wb") as buffer:
            buffer.write(logo.file.read())

        new_company.logo = str(logo_path)

    db.add(new_company)
    db.commit()
    db.refresh(new_company)
    return new_company

# Get all the companies
@router.get("/all-companies", response_model=List[CompanyOut])
def get_all_companies(
    current_user: user_dependency, 
    db: Session = Depends(get_db)):

    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized! Only Admin can See this.")

    companies = db.query(Company).all()
    return companies

# get all company name
@router.get("/all-companies/name")
def get_all_companies(
    current_user: user_dependency, 
    db: Session = Depends(get_db)):

    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized! Only Admin can See this.")

    companies = db.query(Company).options(load_only(Company.name)).all()
    return companies

# Get company info by id
@router.get("/companies/{company_id}", response_model=CompanyOut)
def get_company(company_id: int, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company

# Edit company info (name and ABN not editable)
@router.put("/companies/{company_id}", response_model=CompanyOut)
async def edit_company(
    company_id: int,
    name: str = Form(None),
    web: str = Form(None),
    phone: str = Form(None),
    email: str = Form(None),
    address: str = Form(None),
    logo: UploadFile = File(None),  # Logo upload is optional
    db: Session = Depends(get_db)
):
    db_company = db.query(Company).filter(Company.id == company_id).first()
    if not db_company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Update company fields
    db_company.name = name or db_company.name
    db_company.web = web or db_company.web
    db_company.phone = phone or db_company.phone
    db_company.email = email or db_company.email
    db_company.address = address or db_company.address

    # Save the new logo if uploaded
    if logo:
        # Delete the old logo file if it exists
        if db_company.logo:
            old_logo_path = Path(db_company.logo)
            if old_logo_path.exists():
                old_logo_path.unlink()

        logo_dir = Path("uploads/logos/") / db_company.name
        logo_dir.mkdir(parents=True, exist_ok=True)
        logo_path = logo_dir / logo.filename

        with open(logo_path, "wb") as buffer:
            buffer.write(logo.file.read())

        db_company.logo = str(logo_path)

    db.commit()
    db.refresh(db_company)
    return db_company

# Delete company
@router.delete("/companies/{company_id}")
def delete_company(company_id: int, db: Session = Depends(get_db)):
    db_company = db.query(Company).filter(Company.id == company_id).first()
    if not db_company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Delete the logo file if it exists
    if db_company.logo:
        logo_path = Path(db_company.logo)
        if logo_path.exists():
            logo_path.unlink()
    
    # Delete the associated user data
    users = db.query(User).join(Client, User.id == Client.user_id).filter(Client.company_id == company_id).all()
    users.extend(db.query(User).join(Staff, User.id == Staff.user_id).filter(Staff.company_id == company_id).all())

    for user in users:
        db.delete(user)

    db.delete(db_company)
    db.commit()
    return {"detail": "Company deleted successfully"}

# Get company logo
@router.get("/companies/{company_id}/logo")
def get_company_logo(company_id: int, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company or not company.logo:
        raise HTTPException(status_code=404, detail="Logo not found")

    return FileResponse(company.logo)


















# current user scheme

    # current_user: UserRead = Depends(get_current_user),
    ## current_user: user_dependency,
    ## db: Session = Depends(get_db)