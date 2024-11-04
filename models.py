from sqlalchemy import Column, Integer, Text, ForeignKey, Date, Time, Float, Boolean, DateTime
from sqlalchemy.orm import relationship
from database import Base
import enum
from datetime import datetime

class UserRole(enum.Enum):
    admin = "admin"
    staff = "staff"
    client = "client"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(Text, unique=True, index=True, nullable=False)
    password = Column(Text, nullable=False)
    password_hash = Column(Text, nullable=False)
    role = Column(Text, nullable=False, default=UserRole.staff.value)

    # Relationships
    client = relationship("Client", uselist=False, back_populates="user", cascade="all, delete-orphan")
    staff = relationship("Staff", uselist=False, back_populates="user", cascade="all, delete-orphan")

class Client(Base):
    __tablename__ = "clients"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)
    reference = Column(Text, nullable=True)
    date_of_reg = Column(Date, nullable=True) # registration date by us

    plan_start_date = Column(Date, nullable=True) # new column for plan start date
    plan_end_date = Column(Date, nullable=True) # new column for plan end date

    
    image_path = Column(Text, nullable=True)

    # personal details
    surname = Column(Text, nullable=True)
    given_name = Column(Text, nullable=True)
    preferred_name = Column(Text, nullable=True)
    sex = Column(Text, nullable=True)
    aboriginal = Column(Boolean, nullable=True)
    date_of_birth = Column(Date, nullable=True)
    # residential details
    residence_street = Column(Text, nullable=True) # number or street of residence
    residence_state = Column(Text, nullable=True)
    residence_postcode = Column(Text, nullable=True)
    # postal details
    postal_street = Column(Text, nullable=True) # number or street of postal address
    postal_state = Column(Text, nullable=True)
    postal_postcode = Column(Text, nullable=True)
    
    # contact details
    home_mobile = Column(Text, nullable=True) # changed mobile_phone to home_mobile
    home_phone = Column(Text, nullable=True)
    home_email = Column(Text, nullable=True) # renamed email to home_email in model and db
    
    # ndis info ndi no. previously included
    ndi = Column(Text, unique=True, nullable=False) # ndis
    ndis_start_date = Column(Date, nullable=True)
    ndis_end_date = Column(Date, nullable=True)
    ndis_plan_review_date = Column(Date, nullable=True) # added plan review date in model and db
    funding_type = Column(Text, nullable=True) # plan managed, self managed, ndi-managed, other
        # if plan managed
    plan_provider_name = Column(Text, nullable=True)
    plan_provider_email = Column(Text, nullable=True)
    plan_provider_phone = Column(Text, nullable=True)

    registered_other_ndis = Column(Boolean, nullable=True)
    service_received_other_ndis = Column(Text, nullable=True) # if service received from other ndis
    
    # advocate/representative details
    adv_surname = Column(Text, nullable=True)
    adv_given_name = Column(Text, nullable=True)
    adv_relationship = Column(Text, nullable=True)
    adv_phone = Column(Text, nullable=True)
    adv_mobile = Column(Text, nullable=True)
    adv_email = Column(Text, nullable=True)
    adv_address = Column(Text, nullable=True)
    adv_postal_address = Column(Text, nullable=True)

    # other info
    birth_country = Column(Text, nullable=True)
    main_language = Column(Text, nullable=True)
    lang_interpreter_required = Column(Boolean, nullable=True)
    cultural_bariers = Column(Boolean, nullable=True) # cultural/communication
        
        # if cultural/communication bariers

        # if verbal_communication
    verbal_communication = Column(Text, nullable=True) # added verbal_communication in model and db # yes or no
    interpreter_needed = Column(Boolean, nullable=True) # added interpreter_needed in model and db # yes or no
    interpreter_language = Column(Text, nullable=True) # added interpreter_language in model and db

    cultural_values = Column(Text, nullable=True)
    cultural_behaviours = Column(Text, nullable=True)
    communication_literacy = Column(Text, nullable=True) # written communication/literacy

    # physical profile
    weight = Column(Float, nullable=True)
    height = Column(Float, nullable=True)
    eye_color = Column(Text, nullable=True)
    complexion = Column(Text, nullable=True) # body color
    build = Column(Text, nullable=True) # body size
    hair_color = Column(Text, nullable=True)
    facial_hair = Column(Text, nullable=True)
    birth_marks = Column(Boolean, nullable=True)
    tattos = Column(Boolean, nullable=True)

    # emergency details primary
    emergency1_name = Column(Text, nullable=True)
    emergency1_relationship = Column(Text, nullable=True)
    emergency1_mobile = Column(Text, nullable=True)
    emergency1_phone = Column(Text, nullable=True)

    # emergency details secondary
    emergency2_name = Column(Text, nullable=True)
    emergency2_relationship = Column(Text, nullable=True)
    emergency2_mobile = Column(Text, nullable=True)
    emergency2_phone = Column(Text, nullable=True)

    # gp medical contact
    gp_clinic_name = Column(Text, nullable=True)
    gp_firstname = Column(Text, nullable=True)
    gp_surname = Column(Text, nullable=True)
    gp_email = Column(Text, nullable=True)
    gp_address = Column(Text, nullable=True)
    gp_phone = Column(Text, nullable=True)
    gp_mobile = Column(Text, nullable=True)

    # support coordination details
    support_contact_name = Column(Text, nullable=True)
    support_relationship = Column(Text, nullable=True)
    support_mobile = Column(Text, nullable=True)
    support_phone = Column(Text, nullable=True)

    # specialist medical contact
    have_specialist = Column(Boolean, nullable=True)
    specialist_clinic_name = Column(Text, nullable=True)
    specialist_email = Column(Text, nullable=True)
    specialist_firstname = Column(Text, nullable=True)
    specialist_surname = Column(Text, nullable=True)
    specialist_address = Column(Text, nullable=True)
    specialist_mobile = Column(Text, nullable=True)
    specialist_phone = Column(Text, nullable=True)

    # living and support arrangements
    living_arrangement = Column(Text, nullable=True) # other_arrangement also included here
    # other_arrangement = Column(Text, nullable=True) # if type others

    # travel
    travel = Column(Text, nullable=True) # other_travel also included here
    # disability
    disability = Column(Text, nullable=True)
    # important people in the Participant’s life such as family member and their relationship?
    important_people = Column(Text, nullable=True) # added important_people in the model and db # important_people and their relationship also included here

    # Relationships
    user = relationship("User", back_populates="client")
    company = relationship("Company", back_populates="client")
    tasks = relationship("Task", back_populates="client", cascade="all, delete-orphan")
 
class Staff(Base):
    __tablename__ = "staffs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    date_of_reg = Column(Date, nullable=True) # added date of registration in model and db
    image_path = Column(Text, nullable=True)
    
    # personale details
    title = Column(Text, nullable=True)
    given_name = Column(Text, nullable=True)
    surname = Column(Text, nullable=True)
    preferred_name = Column(Text, nullable=True)
    dob = Column(Date, nullable=True) # date of birth
    # residential address details   
    residence_street = Column(Text, nullable=True) # number/street
    residence_state = Column(Text, nullable=True)
    residence_postcode = Column(Text, nullable=True)
    # postal address details
    postal_street = Column(Text, nullable=True) # number/street
    postal_state = Column(Text, nullable=True)
    postal_postcode = Column(Text, nullable=True)
    # contact details
    home_email = Column(Text, nullable=True)
    home_phone = Column(Text, nullable=True)
    home_mobile = Column(Text, nullable=True)
    # emergency details primary
    emergency1_name = Column(Text, nullable=True)
    emergency1_relationship = Column(Text, nullable=True)
    emergency1_mobile = Column(Text, nullable=True)
    emergency1_phone = Column(Text, nullable=True)
    # emergency details secondary
    emergency2_name = Column(Text, nullable=True)
    emergency2_relationship = Column(Text, nullable=True)
    emergency2_mobile = Column(Text, nullable=True)
    emergency2_phone = Column(Text, nullable=True)
    # bank details
        # primary bank details
    bank1_name = Column(Text, nullable=True)
    bank1_acc_name = Column(Text, nullable=True)
    bank1_acc_no = Column(Text, nullable=True)
    bank1_branch = Column(Text, nullable=True)
    bank1_bsb = Column(Text, nullable=True)
        # secondary bank details
    bank2_name = Column(Text, nullable=True)
    bank2_acc_name = Column(Text, nullable=True)
    bank2_acc_no = Column(Text, nullable=True)
    bank2_branch = Column(Text, nullable=True)
    bank2_bsb = Column(Text, nullable=True)

    bank_unit = Column(Text, nullable=True)
    bank_amount = Column(Float, nullable=True)
    bank_percent_net_pay = Column(Float, nullable=True)
    # other info
    employee_tax = Column(Text, nullable=True)
    abn = Column(Text, nullable=True)
    # secondary employment(not mandatory)
    secondary_employment = Column(Boolean, nullable=True)
    secondary_employment_details = Column(Text, nullable=True) # if secondary_employment is true
    # health details(optional)
    epilepsy = Column(Boolean, nullable=True)
    diabetes = Column(Boolean, nullable=True)
    diabetes_type = Column(Text, nullable=True) # if diabetes is true
    heart_condition = Column(Boolean, nullable=True)
    heart_condition_details = Column(Text, nullable=True) # if heart_condition is true
    allergies = Column(Boolean, nullable=True)
    allergies_details = Column(Text, nullable=True) # if allergies is true
    health_others = Column(Boolean, nullable=True)
    health_others_details = Column(Text, nullable=True) # if others is true

    # visa info
    australian = Column(Boolean, nullable=True)
        # not australian
    aus_permanent = Column(Boolean, nullable=True)
    have_working_visa = Column(Boolean, nullable=True)
    visa_expiary_date = Column(Date, nullable=True)
    visa_restrictions = Column(Text, nullable=True)

    # Relationships
    user = relationship("User", back_populates="staff")
    company = relationship("Company", back_populates="staff")
    tasks = relationship("Task", back_populates="staff", cascade="all, delete-orphan")

class Company(Base):
    __tablename__ = "companies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(Text, unique=True, nullable=False)
    web = Column(Text, nullable=True)
    phone = Column(Text, nullable=False)
    email = Column(Text, nullable=False)
    address = Column(Text, nullable=True)
    abn = Column(Text, unique=True, nullable=False)
    logo = Column(Text, nullable=True)

    # Relationships
    client = relationship("Client", back_populates="company", cascade="all, delete-orphan")
    staff = relationship("Staff", back_populates="company", cascade="all, delete-orphan")


class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    staff_id = Column(Integer, ForeignKey("staffs.id"), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    start_date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_date = Column(Date, nullable=False)
    end_time = Column(Time, nullable=False)
    service_type = Column(Text, nullable=False)
    hours = Column(Float, nullable=False, default=0)
    done = Column(Boolean, default=False)
    approved = Column(Boolean, default=False)
    tasks_list = Column(Text, nullable=True)
    done_time = Column(DateTime, nullable=True)

    # Relationships
    staff = relationship("Staff", back_populates="tasks")
    client = relationship("Client", back_populates="tasks")
    medias = relationship("Media", back_populates="task", cascade="all, delete-orphan")

    @staticmethod
    def calculate_hours(start_date, start_time, end_date, end_time):
        start = datetime.combine(start_date, start_time)
        end = datetime.combine(end_date, end_time)
        # >>> added this in the route
        # if end < start:
        #     raise ValueError("End time must be after start time")
        # <<<<
        return (end - start).total_seconds() / 3600

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.hours = self.calculate_hours(
            self.start_date, self.start_time,
            self.end_date, self.end_time
        )

class Media(Base):
    __tablename__ = "media"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    file_path = Column(Text, nullable=False)

    # Relationship
    task = relationship("Task", back_populates="medias")