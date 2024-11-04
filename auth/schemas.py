from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from enum import Enum
from datetime import date, time, datetime
from decimal import Decimal
from fastapi import File, UploadFile

class UserRole(str, Enum):
    admin = "admin"
    staff = "staff"
    client = "client"

class UserCreate(BaseModel):
    username: str
    # name: Optional[str]  # Name is now optional
    # phone: Optional[str]  # Phone is also optional
    # email: EmailStr
    role: UserRole
    password: str

class UserRead(BaseModel):
    id: int
    username: str
    # email: EmailStr
    role: UserRole  # Use the Enum to match the type with the role

    class Config:
        orm_mode = True

class UserUpdate(BaseModel):
    username: Optional[str] = None
    # name: Optional[str] = None
    # phone: Optional[str] = None
    # email: Optional[str] = None
    role: Optional[str] = None

# >>>>>> adding a route to get all users with username, name, phone, email, company, role
class ReadUserDetails(UserRead):
    name: Optional[str]
    mobile: Optional[str]
    email: Optional[str]
    company_name: Optional[str]


# >>>>>> commenting old client schemas
# class ClientCreate(BaseModel):
#     # username: str
#     address: Optional[str] = None
#     disability: Optional[str] = None
#     # >>>> adding additional fields
#     ndi: str
#     reference: Optional[str]
#     company_name: Optional[str]

# class ClientRead(BaseModel):
#     id: int
#     name: str
#     phone: Optional[str]
#     email: EmailStr
#     address: str
#     disability: Optional[str]

#     class Config:
#         orm_mode = True

# class ClientUpdate(BaseModel):
#     address: Optional[str] = None
#     disability: Optional[str] = None
#     ndi: str
#     reference: Optional[str]
#     company_name: Optional[str]


# >>>> updating taskcreate model because we used it to edit task also
# class TaskCreate(BaseModel):
#     start_date: date
#     start_time: time
#     end_date: date
#     end_time: time
#     service_type: str

# class ReadClientDetail(ClientBase):
#     id: int
#     username: str
#     role: str
#     name: str
#     phone: str
#     email: Optional[str] = None
#     address: Optional[str] = None
#     disability: Optional[str] = None

# Since you're using the TaskCreate schema for updating tasks, you should also allow optional fields in the TaskCreate schema. Otherwise, every field is required when editing a task, which might not be desirable.
class TaskCreate(BaseModel):
    start_date: Optional[date] = None
    start_time: Optional[time] = None
    end_date: Optional[date] = None
    end_time: Optional[time] = None
    service_type: Optional[str] = None
    # adding this new field to add tasks_list functionality
    tasks_list: Optional[str] = None  # New field

class TaskRead(BaseModel):
    id: int
    # timesheet_id: Optional[int] # getting rid of timesheet_id for new db
    staff_id: int
    client_id: int
    start_date: date
    start_time: time
    end_date: date
    end_time: time
    hours: Decimal  # New field for hours
    service_type: str
    # done: bool  # New field for task completion
    # approved: bool  # New field for client approval
    done: Optional[bool] = None
    approved: Optional[bool] = None
    # updating to add done_time and tasks_list
    tasks_list: Optional[str] = None  # New field
    done_time: Optional[datetime] = None  # New field

    class Config:
        orm_mode = True

class TaskStatusUpdate(BaseModel):
    done: bool

class TaskReadDetails(TaskRead):
    staff_name: Optional[str]  # Add staff_name field
    client_name: Optional[str]  # Add client_name field
    media_files: Optional[list] = []

## commenting timesheet schemas
# class TimesheetCreate(BaseModel):
#     week_start_date: str

# class TimesheetRead(BaseModel):
#     id: int
#     staff_id: int
#     week_start_date: str
#     tasks: list[TaskRead] = []  # Include tasks in the timesheet

#     class Config:
#         orm_mode = True

class MediaCreate(BaseModel):
    task_id: int
    file_path: str

class MediaRead(BaseModel):
    id: int
    task_id: int
    file_path: str

    class Config:
        orm_mode = True
  
# for reading media
class MediaRead(BaseModel):
    id: int
    task_id: int
    file_path: str

    class Config:
        orm_mode = True

# >>>>>>>>>> schemas for company
from pydantic import BaseModel, EmailStr, HttpUrl, constr
class CompanyBase(BaseModel):
    # web: Optional[HttpUrl]
    web: Optional[str]
    phone: Optional[str]
    email: Optional[EmailStr]
    address: Optional[str]
    logo: Optional[str]

class CompanyCreate(CompanyBase):
    name: str # modified instead of constr(min_length=1)
    abn: str # modified instead of constr(min_length=1)

class CompanyUpdate(CompanyBase):
    pass

class CompanyOut(CompanyBase):
    id: int
    name: str
    abn: str

    class Config:
        orm_mode = True


# # >>>>>> schemas for staff crud for new db
# >>>>> modifying this with the added columns in new db
# class StaffBase(BaseModel):
#     # company_id: int
#     address: Optional[str] = None

#     class Config:
#         orm_mode = True

# class StaffCreate(BaseModel):
#     # user_id: int
#     address: Optional[str] = None
#     company_name: str

# class StaffUpdate(BaseModel):
#     # company_id: Optional[int] = None
#     company_id: int
#     address: Optional[str] = None

#     class Config:
#         orm_mode = True

# class StaffRead(StaffBase):
#     id: int
#     user_id: int

#     class Config:
#         orm_mode = True

# >>>>> new client schemas
class ClientBase(BaseModel):
    # user_id: int
    # address: Optional[str] = None # droppped addres from model and db
    company_id: Optional[int] = None
    reference: Optional[str] = None
    # date_of_reg: Optional[date] = None # updating schema for dry
    plan_start_date: Optional[date] = None
    plan_end_date: Optional[date] = None
    image_path: Optional[str] = None
    
    given_name: Optional[str] = None
    surname: Optional[str] = None
    preferred_name: Optional[str] = None
    sex: Optional[str] = None
    aboriginal: Optional[bool] = False
    date_of_birth: Optional[date] = None
    residence_street: Optional[str] = None
    residence_state: Optional[str] = None
    residence_postcode: Optional[str] = None
    postal_street: Optional[str] = None
    postal_state: Optional[str] = None
    postal_postcode: Optional[str] = None
    home_mobile: Optional[str] = None # renamed mobile_phone to home_mobile in db and model
    home_phone: Optional[str] = None
    home_email: Optional[EmailStr] = None
    
    # ndi: str  # changed this for the clientbase model
    ndis_start_date: Optional[date] = None
    ndis_end_date: Optional[date] = None
    ndis_plan_review_date: Optional[date] = None # added ndis_plan_review_date model and db
    funding_type: Optional[str] = None
    plan_provider_name: Optional[str] = None
    plan_provider_email: Optional[EmailStr] = None
    plan_provider_phone: Optional[str] = None
    registered_other_ndis: Optional[bool] = False
    service_received_other_ndis: Optional[str] = None
    adv_surname: Optional[str] = None
    adv_given_name: Optional[str] = None
    adv_relationship: Optional[str] = None
    adv_phone: Optional[str] = None
    adv_mobile: Optional[str] = None
    adv_email: Optional[EmailStr] = None
    adv_address: Optional[str] = None
    adv_postal_address: Optional[str] = None
    birth_country: Optional[str] = None
    main_language: Optional[str] = None
    lang_interpreter_required: Optional[bool] = False
    cultural_bariers: Optional[bool] = False

    verbal_communication: Optional[str] = None # added verbal_communication in model, db and schema
    interpreter_needed: Optional[bool] = False # added interpreter_needed in model, db and schema
    interpreter_language: Optional[str] = None # added interpreter_language in model, db and schema

    cultural_values: Optional[str] = None
    cultural_behaviours: Optional[str] = None
    communication_literacy: Optional[str] = None
    weight: Optional[float] = None
    height: Optional[float] = None
    eye_color: Optional[str] = None
    complexion: Optional[str] = None
    build: Optional[str] = None
    hair_color: Optional[str] = None
    facial_hair: Optional[str] = None
    birth_marks: Optional[bool] = False
    tattos: Optional[bool] = False
    emergency1_name: Optional[str] = None
    emergency1_relationship: Optional[str] = None
    emergency1_mobile: Optional[str] = None
    emergency1_phone: Optional[str] = None
    emergency2_name: Optional[str] = None
    emergency2_relationship: Optional[str] = None
    emergency2_mobile: Optional[str] = None
    emergency2_phone: Optional[str] = None
    gp_clinic_name: Optional[str] = None
    gp_firstname: Optional[str] = None
    gp_surname: Optional[str] = None
    gp_email: Optional[EmailStr] = None
    gp_address: Optional[str] = None
    gp_phone: Optional[str] = None
    gp_mobile: Optional[str] = None
    support_contact_name: Optional[str] = None
    support_relationship: Optional[str] = None
    support_mobile: Optional[str] = None
    support_phone: Optional[str] = None
    have_specialist: Optional[bool] = False 
    specialist_clinic_name: Optional[str] = None
    specialist_email: Optional[EmailStr] = None
    specialist_firstname: Optional[str] = None
    specialist_surname: Optional[str] = None
    specialist_address: Optional[str] = None
    specialist_mobile: Optional[str] = None
    specialist_phone: Optional[str] = None
    living_arrangement: Optional[str] = None
    travel: Optional[str] = None
    disability: Optional[str] = None
    important_people: Optional[str] = None # added important_people in model, db and schema

    class Config:
        orm_mode = True

    
class ClientCreate(ClientBase):
    ndi: str
    date_of_reg: date
    image: Optional[str] = None
    # surname: Optional[str] = None # updating schema for dry
    # given_name: Optional[str] = None # updating schema for dry

class ClientUpdate(ClientBase):
    pass

class ClientRead(ClientBase):
    id: int
    user_id: int
    date_of_reg: Optional[date] = None
    ndi: str

class ReadClientDetails(ClientRead):
    name: Optional[str] = None
    role: Optional[str] = 'client'
    
    class Config:
        orm_mode = True
        from_attributes = True

class ReadClientInfo(BaseModel):
    id: int
    user_id: int
    # date_of_reg: Optional[date] = None
    username: Optional[str]
    name: Optional[str]
    email: Optional[str]
    mobile: Optional[str]

# >>>>> adding new columns to the staff schema

class StaffBase(BaseModel):
    # Basic fields shared across schemas
    company_id: int
    # address: Optional[str] = None # dropped address column from model, db, schema
    date_of_reg: Optional[date] = None # added date_of_reg in model, db and schema
    # image_path: Optional[str] = None

    title: Optional[str] = None
    surname: Optional[str] = None
    given_name: Optional[str] = None
    preferred_name: Optional[str] = None
    date_of_birth: Optional[date] = None # changed from dob to date_of_birth in schema only
    residence_street: Optional[str] = None
    residence_state: Optional[str] = None
    residence_postcode: Optional[str] = None
    postal_street: Optional[str] = None
    postal_state: Optional[str] = None
    postal_postcode: Optional[str] = None
    home_email: Optional[str] = None
    home_phone: Optional[str] = None
    home_mobile: Optional[str] = None
    emergency1_name: Optional[str] = None
    emergency1_relationship: Optional[str] = None
    emergency1_mobile: Optional[str] = None
    emergency1_phone: Optional[str] = None
    emergency2_name: Optional[str] = None
    emergency2_relationship: Optional[str] = None
    emergency2_mobile: Optional[str] = None
    emergency2_phone: Optional[str] = None
    bank1_name: Optional[str] = None
    bank1_acc_name: Optional[str] = None
    bank1_acc_no: Optional[str] = None
    bank1_branch: Optional[str] = None
    bank1_bsb: Optional[str] = None
    bank2_name: Optional[str] = None
    bank2_acc_name: Optional[str] = None
    bank2_acc_no: Optional[str] = None
    bank2_branch: Optional[str] = None
    bank2_bsb: Optional[str] = None
    bank_unit: Optional[str] = None
    bank_amount: Optional[float] = None
    bank_percent_net_pay: Optional[float] = None
    employee_tax: Optional[str] = None
    abn: Optional[str] = None
    secondary_employment: Optional[bool] = False
    secondary_employment_details: Optional[str] = None
    epilepsy: Optional[bool] = False
    diabetes: Optional[bool] = False
    diabetes_type: Optional[str] = None
    heart_condition: Optional[bool] = False
    heart_condition_details: Optional[str] = None
    allergies: Optional[bool] = False
    allergies_details: Optional[str] = None
    health_others: Optional[bool] = False
    health_others_details: Optional[str] = None
    australian: Optional[bool] = False
    aus_permanent: Optional[bool] = False
    have_working_visa: Optional[bool] = False
    visa_expiary_date: Optional[date] = None
    visa_restrictions: Optional[str] = None

    class Config:
        orm_mode = True

class StaffCreate(StaffBase):
    # company_name: str
    # Including fields specific to staff creation
    # company_id: Optional[int] = None
    image: Optional[str] = None,
    pass

class StaffUpdate(StaffBase):
    company_id: Optional[int] = None

    class Config:
        orm_mode = True

class StaffRead(StaffBase):
    id: int
    user_id: int
    company_id: Optional[int] = None

    class Config:
        orm_mode = True

class ReadStaffInfo(BaseModel):
    id: int
    username: str
    name: str
    email: Optional[str]
    mobile: Optional[str]

class ReadStaffDetail(BaseModel):
    user_id: int
    staff_id: int
    username: str
    role: str
    name: Optional[str]
    image_path: Optional[str]
    company_id: int
    address: Optional[str] = None
    # Personal details
    title: Optional[str] = None
    surname: Optional[str] = None
    given_name: Optional[str] = None
    preferred_name: Optional[str] = None
    date_of_birth: Optional[date] = None # changed from dob to date_of_birth in schema only
    # Residential address details
    residence_street: Optional[str] = None
    residence_state: Optional[str] = None
    residence_postcode: Optional[str] = None
    # Postal address details
    postal_street: Optional[str] = None
    postal_state: Optional[str] = None
    postal_postcode: Optional[str] = None
    # Contact details
    home_email: Optional[str] = None
    home_phone: Optional[str] = None
    home_mobile: Optional[str] = None
    # Emergency details primary
    emergency1_name: Optional[str] = None
    emergency1_relationship: Optional[str] = None
    emergency1_mobile: Optional[str] = None
    emergency1_phone: Optional[str] = None
    # Emergency details secondary
    emergency2_name: Optional[str] = None
    emergency2_relationship: Optional[str] = None
    emergency2_mobile: Optional[str] = None
    emergency2_phone: Optional[str] = None
    # Bank details
    # Primary bank details
    bank1_name: Optional[str] = None
    bank1_acc_name: Optional[str] = None
    bank1_acc_no: Optional[str] = None
    bank1_branch: Optional[str] = None
    bank1_bsb: Optional[str] = None
    # Secondary bank details
    bank2_name: Optional[str] = None
    bank2_acc_name: Optional[str] = None
    bank2_acc_no: Optional[str] = None
    bank2_branch: Optional[str] = None
    bank2_bsb: Optional[str] = None
    bank_unit: Optional[str] = None
    bank_amount: Optional[Decimal] = None
    bank_percent_net_pay: Optional[Decimal] = None
    # Other info
    employee_tax: Optional[str] = None
    abn: Optional[str] = None
    # Secondary employment (not mandatory)
    secondary_employment: Optional[bool] = None
    secondary_employment_details: Optional[str] = None  # if secondary_employment is true
    # Health details (optional)
    epilepsy: Optional[bool] = None
    diabetes: Optional[bool] = None
    diabetes_type: Optional[str] = None  # if diabetes is true
    heart_condition: Optional[bool] = None
    heart_condition_details: Optional[str] = None  # if heart_condition is true
    allergies: Optional[bool] = None
    allergies_details: Optional[str] = None  # if allergies is true
    health_others: Optional[bool] = None
    health_others_details: Optional[str] = None  # if others is true
    # Visa info
    australian: Optional[bool] = None
    aus_permanent: Optional[bool] = None  # if not australian
    have_working_visa: Optional[bool] = None  # if not australian
    visa_expiary_date: Optional[date] = None  # if not australian
    visa_restrictions: Optional[str] = None  # if not australian