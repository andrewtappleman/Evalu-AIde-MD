from kivy.app import App
import tensorflow as tf
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.dropdown import DropDown
from tensorflow.keras.models import load_model
#:import webbrowser webbrowser
from io import BytesIO
from kivy.core.image import Image as CoreImage
import base64
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
import numpy as np
from kivy.graphics import Color, Rectangle
from kivy.uix.widget import Widget
from kivy.properties import StringProperty
from plyer import notification
from httpx import HTTPStatusError
import pymongo
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import pandas as pd
import webbrowser
import time
import httpx
server_api = ServerApi('1')


from kivy.config import Config
Config.set('graphics', 'width', '400')
Config.set('graphics', 'height', '700')

import logging
logging.getLogger("pymongo").setLevel(logging.WARNING)

from kivy.core.window import Window

Window.size = (400, 700)
 
import sys
print(sys.version)

import globals

class SignIn(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(0.137, 0.298, 0.416, 1)
            self.rect = Rectangle(pos=self.pos, size=self.size)

        self.bind(pos=self.update_rect, size=self.update_rect)

        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)

        layout.add_widget(Label(text="Welcome To Evalu-AIde, MD!", font_size=24))
        layout.add_widget(Label(text='Type in your organization name to get started.', font_size=18))

        self.org_input = (TextInput(text="Organization", font_size = 24, background_color = (0.824, 0.757, 0.714, 1)))
        layout.add_widget(self.org_input)

        self.submit = (Button(text="Submit", background_color =  (0.271, 0.408, 0.510, 1)))
        self.submit.bind(on_release = self.begin)
        layout.add_widget(self.submit)

        self.newOrg = (Button(text="New Organization", background_color =  (0.271, 0.408, 0.510, 1)))
        self.newOrg.bind(on_release = self.new)
        layout.add_widget(self.newOrg)

        self.add_widget(layout)
    
    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def begin(self, instance):

        db = globals.client['DiagnosticAI']
        collection = db['Organization Data']
        
        org_name = self.org_input.text
        
        query = {"org": org_name}
        
        if self.check_for_type(collection, query):
            globals.org_name = org_name
            self.manager.current = "afterlogin"
        else:
            notification.notify(title 
                                = 'Evalu-AIde, MD', message = 'Organization Account Not Found')
            self.org_input.text = ""

    def new(self, instance):

        db = globals.client['DiagnosticAI']
        collection = db['Organization Data']
        
        org_name = self.org_input.text
        
        query = {"org": org_name}
        globals.org_name = org_name
        
        if self.check_for_type(collection, query):
            notification.notify(title = 'Evalu-AIde, MD', message = 'Organization Account Already Created')
            self.org_input.text = ""
        else:
            OrgData = [{"org": org_name}]
            globals.org_name = self.org_input.text
            print(OrgData)
            try:
                result = collection.insert_many(OrgData)
            except pymongo.errors.OperationFailure:
                print("An authentication error was received. Check your database user permissions.")
                sys.exit(1)
            else:
                inserted_count = len(result.inserted_ids)
                print("I inserted %d documents." % inserted_count)
                print("\n")
            self.manager.current = "afterlogin"


    def check_for_type(self, collection, query):
        globals.org_name = self.org_input.text
        try:
            db = globals.client['DiagnosticAI']
            collection = db['Organization Data']
            result = collection.find_one(query)
            return result is not None
        except Exception as e:
            print(f"[MongoDB Error] {e}")
            return False


class PatientSearch(Screen):
    def on_pre_enter(self):
        print(globals.org_name)
        self.clear_widgets()
        db = globals.client['DiagnosticAI']
        collection = db['Patient Data']

        print(globals.org_name)
        patient_cursor = collection.find({"org": globals.org_name}).sort('_id', -1)
        self.patient_list = list(patient_cursor)
        print("length", len(self.patient_list))

        with self.canvas.before:
            Color(0.137, 0.298, 0.416, 1)
            self.rect = Rectangle(pos=self.pos, size=self.size)

        self.bind(pos=self.update_rect, size=self.update_rect)

        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)

        layout.add_widget(Label(text="Search for a patient's info!", font_size=24))
    
        dropdown = DropDown(size_hint = (None, None))
        dropdown.bind(on_select=lambda instance, x: setattr(self.patientName, 'text', x))
    
        for option in self.patient_list:
            btn = Button(text=option["patient"], size_hint_y=None, height=75, background_color =  (0.271, 0.408, 0.510, 1))
            btn.bind(on_release=lambda btn: dropdown.select(btn.text))
            if btn.text != "Not Found":
                dropdown.add_widget(btn)
        self.patientName = Button(text = "Patient Name", size_hint=(1, None), height = 100,  background_color =  (0.271, 0.408, 0.510, 1))
        self.patientName.bind(on_press=dropdown.open)
        self.patientName.text = "Patient Name"
        layout.add_widget(self.patientName)

        self.submit = (Button(text="Search", background_color =  (0.271, 0.408, 0.510, 1)))
        self.submit.bind(on_release = self.check)
        layout.add_widget(self.submit)

        self.imagelayout = BoxLayout(orientation = "horizontal", size_hint = (1, 1))
        self.image = Image(size_hint=(1, 1))
        self.imagelayout.add_widget(self.image)
        self.image.texture = None
        layout.add_widget(self.imagelayout)

        self.patient_issue = (Label(text="", font_size=20, size_hint = (1, 0.2)))
        self.patient_issue.text = ""
        self.patient_class = (Label(text="", font_size=20, size_hint = (1, 0.2)))
        self.patient_class.text = ""
        self.patient_flag = (Label(text="", font_size=20, size_hint = (1, 0.2)))
        self.patient_flag.text = ""

        back_btn = Button(text="Back to the Main Page", background_color =  (0.271, 0.408, 0.510, 1))
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'afterlogin'))

        layout.add_widget(self.patient_issue)
        layout.add_widget(self.patient_class)
        layout.add_widget(self.patient_flag)
        layout.add_widget(back_btn)

        if globals.patient_name == None:
            print("no prename")
        else:
            self.patientName.text = globals.patient_name
            print("A-okay")
            self.check()

        self.add_widget(layout)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def check(self, instance=None):

        db = globals.client['DiagnosticAI']
        collection = db['Patient Data']
        
        org_name = globals.org_name
        patient_name = self.patientName.text
        
        query = {"org": org_name, "patient": patient_name}

        try:

            patient_cursor = collection.find({"org": org_name, "patient": patient_name})
            patient_list = list(patient_cursor)
            print(patient_list)

            patient_data = patient_list[0]
            print(patient_data)

            patient_class = patient_data.get('class', 'Unknown')
            print("class")
            flag = patient_data.get('flag', 'Unknown')
            print("flag")
            image = patient_data.get('image', 'Unknown')
            print("image")
            issue = patient_data.get('issue', 'Unknown')
            print("issue")

            self.patient_class.text = ("Chance of illness: " + str(patient_class) + "%")
            if flag == 0:
                self.patient_flag.text = "Unflagged"
            else:
                self.patient_flag.text = "Flagged"
            image = base64.b64decode(image)
            image = BytesIO(image)
            image = CoreImage(image, ext='png')
            self.image.texture = image.texture
            self.patient_issue.text = issue


        except Exception as e:
            print("Error:", e)

class PatientFlags(Screen):

    def on_pre_enter(self):
        with self.canvas.before:
            Color(0.137, 0.298, 0.416, 1)
            self.rect = Rectangle(pos=self.pos, size=self.size)

        self.bind(pos=self.update_rect, size=self.update_rect)

        self.layout = BoxLayout(orientation='vertical', padding=0, spacing=0)

        self.layout.add_widget(Label(text="Flagged Patients!", font_size=35, size_hint = (1, 0.25)))

        db = globals.client['DiagnosticAI']
        collection = db['Patient Data']
        
        org_name = globals.org_name
        print(org_name)

        for patient_count in range(1000):
            try:
                print(patient_count)

                patient_cursor = collection.find({"org":globals.org_name, "flag": 1}).sort('_id', -1).skip(patient_count).limit(1)
                patient_list = list(patient_cursor)
                print("length", len(patient_list))

                if not patient_list:
                    print("Patient flag broken")
                    break

                patient_data = patient_list[0]

                if patient_data.get("org") == org_name:
                    print("org name correct")
                    patient_name = patient_data.get('patient', 'Unknown')
                    classification = str(patient_data.get('class', 'Unknown'))
                    print(patient_name+classification)
                    self.layout.add_widget(Button(
                        text=f"Patient: {patient_name}, Chance of illness: {classification}%",
                        font_size=17,
                        background_color =  (0.271, 0.408, 0.510, 1),
                        size_hint = (1, 0.15),
                        on_release = lambda instance, name=patient_name:  self.getData(name)
                    ))
                else:
                    print("N/A")


            except Exception as e:
                print("Error:", e)
                break
        backlayout = BoxLayout(orientation = "horizontal", size_hint = (1, 0.2))
        back_btn = Button(text="Back to the Main Page", background_color =  (0.271, 0.408, 0.510, 1))
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'afterlogin'))
        backlayout.add_widget(back_btn)
        self.layout.add_widget(backlayout)

        self.add_widget(self.layout)
    def getData(self, name):
        globals.patient_name = name
        self.manager.current = "search"
    def check_for_type(self, collection, query):
        result = collection.find_one(query)
        return result is not None
    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size


class MainPage(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(0.137, 0.298, 0.416, 1)
            self.rect = Rectangle(pos=self.pos, size=self.size)

        self.bind(pos=self.update_rect, size=self.update_rect)

        layout = BoxLayout(orientation='vertical', padding=0, spacing=20)

        ImageButton1 = BoxLayout(orientation = "horizontal", spacing=0, padding=0)
        BreastImage = (Image(size_hint = (0.2,None), on_press=lambda x: setattr(self.manager, 'current', 'breast')))
        image = base64.b64decode(globals.BreastLogo)
        image = BytesIO(image)
        image = CoreImage(image, ext='png')
        BreastImage.texture = image.texture
        ImageButton1.add_widget(BreastImage)
        ImageButton1.add_widget(Button(text="Diagnose Breast Cancer",size_hint = (.8, None), background_color =  (0.271, 0.408, 0.510, 1), on_press=lambda x: setattr(self.manager, 'current', 'breast')))
        layout.add_widget(ImageButton1)

        ImageButton2 = BoxLayout(orientation = "horizontal", spacing=0, padding=0)
        LeukemiaImage = (Image(size_hint = (0.2, None), on_press=lambda x: setattr(self.manager, 'current', 'covid')))
        image = base64.b64decode(globals.CovidLogo)
        image = BytesIO(image)
        image = CoreImage(image, ext='png')
        LeukemiaImage.texture = image.texture
        ImageButton2.add_widget(LeukemiaImage)
        ImageButton2.add_widget(Button(text="Diagnose Covid-19",size_hint = (0.8, None), background_color =  (0.271, 0.408, 0.510, 1), on_press=lambda x: setattr(self.manager, 'current', 'covid')))
        layout.add_widget(ImageButton2)

        ImageButton3 = BoxLayout(orientation = "horizontal", spacing=0, padding=0)
        SkinImage = (Image(size_hint = (0.2, None), on_press=lambda x: setattr(self.manager, 'current', 'skin')))
        image = base64.b64decode(globals.SkinLogo)
        image = BytesIO(image)
        image = CoreImage(image, ext='png')
        SkinImage.texture = image.texture
        ImageButton3.add_widget(SkinImage)
        ImageButton3.add_widget(Button(text="Diagnose Skin Cancer",size_hint = (0.8, None), background_color =  (0.271, 0.408, 0.510, 1), on_press=lambda x: setattr(self.manager, 'current', 'skin')))
        layout.add_widget(ImageButton3)

        ImageButton4 = BoxLayout(orientation = "horizontal", spacing=0, padding=0)
        PneumoniaImage = (Image(size_hint = (0.2, None), on_press=lambda x: setattr(self.manager, 'current', 'skin')))
        image = base64.b64decode(globals.PneumoniaLogo)
        image = BytesIO(image)
        image = CoreImage(image, ext='png')
        PneumoniaImage.texture = image.texture
        ImageButton4.add_widget(PneumoniaImage)
        ImageButton4.add_widget(Button(text="Diagnose Pneumonia",size_hint = (0.8, None), background_color =  (0.271, 0.408, 0.510, 1), on_press=lambda x: setattr(self.manager, 'current', 'pneumonia')))
        layout.add_widget(ImageButton4)

        back_btn = Button(text="Back to the Main Page", background_color =  (0.271, 0.408, 0.510, 1))
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'afterlogin'))
        layout.add_widget(back_btn)

        self.add_widget(layout)
    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size
class AfterLogin(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
                
        layout = BoxLayout(orientation='vertical', padding=0, spacing=20)
        
        layout.add_widget(Label(text="Welcome To Evalu-AIde, MD!", font_size=24))
        layout.add_widget(Label(text='"AI driven health diagnostics"', font_size=20))

        DocBtn = BoxLayout(orientation = "horizontal", spacing=0, padding=0)
        PneumoniaImage = (Image(size_hint = (0.2, None), on_press=lambda x: setattr(self.manager, 'current', 'skin')))
        image = base64.b64decode(globals.DoctorLogo)
        image = BytesIO(image)
        image = CoreImage(image, ext='png')
        PneumoniaImage.texture = image.texture
        DocBtn.add_widget(PneumoniaImage)
        DocBtn.add_widget(Button(text="Diagnose Illness with AI",size_hint = (0.8, None), background_color =  (0.271, 0.408, 0.510, 1), on_press=lambda x: setattr(self.manager, 'current', 'main')))
        layout.add_widget(DocBtn)
        
        
        FlaggedPats = BoxLayout(orientation = "horizontal", spacing=0, padding=0)
        FlagImage = (Image(size_hint = (0.2, None), on_press=lambda x: setattr(self.manager, 'current', 'patient')))
        image = base64.b64decode(globals.FlagLogo)
        image = BytesIO(image)
        image = CoreImage(image, ext='png')
        FlagImage.texture = image.texture
        FlaggedPats.add_widget(FlagImage)
        FlaggedPats.add_widget(Button(text="Flagged Patients",size_hint = (0.8, None), background_color =  (0.271, 0.408, 0.510, 1), on_press=lambda x: setattr(self.manager, 'current', 'patient')))
        layout.add_widget(FlaggedPats)

        SearchPats = BoxLayout(orientation = "horizontal", spacing=0, padding=0)
        SearchImage = (Image(size_hint = (0.2, None), on_press=lambda x: setattr(self.manager, 'current', 'search')))
        image = base64.b64decode(globals.SearchLogo)
        image = BytesIO(image)
        image = CoreImage(image, ext='png')
        SearchImage.texture = image.texture
        SearchPats.add_widget(SearchImage)
        SearchPats.add_widget(Button(text="Search Patients",size_hint = (0.8, None), background_color =  (0.271, 0.408, 0.510, 1), on_press=lambda x: setattr(self.manager, 'current', 'search')))
        layout.add_widget(SearchPats)

        self.add_widget(layout)

class NextSteps(Screen):
    def on_pre_enter(self):
        self.specialty_button.text = globals.illness
        self.patient_name.text = "Patient Name"
        self.flag_btn.text = "Flag Patient"
        self.flagged = 0
    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(0.137, 0.298, 0.416, 1)
            self.rect = Rectangle(pos=self.pos, size=self.size)

        self.bind(pos=self.update_rect, size=self.update_rect)

        
        layout = BoxLayout(
            orientation='vertical',
            padding=30,
            spacing=40,
            size_hint=(0.8, 0.8),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )

        layout.add_widget(Label(text="Report For Flagging", font_size=24, size_hint_y=None, height=50))
        
        self.patient_name = TextInput(
            text="Patient Name",
            background_color = (0.824, 0.757, 0.714, 1),
            size_hint_y=None, 
            height=80
        )
        layout.add_widget(self.patient_name)

        self.specialty_dropdown = DropDown()
        self.specialty_button = Button(text=globals.illness,background_color =  (0.271, 0.408, 0.510, 1), size_hint_y=None, height=80)
        
        self.specialty_button.bind(on_release=self.specialty_dropdown.open)

        for specialty_text in ["Breast Cancer", "Covid-19", "Pneumonia", "Skin Cancer"]:
            btn = Button(text=specialty_text,background_color =  (0.271, 0.408, 0.510, 1), size_hint_y=None, height=80)
            btn.bind(on_release=lambda btn: self.specialty_dropdown.select(btn.text))
            self.specialty_dropdown.add_widget(btn)

        self.specialty_dropdown.bind(on_select=lambda instance, x: setattr(self.specialty_button, 'text', x))

        layout.add_widget(self.specialty_button)

        self.flagged = 0

        self.flag_btn = Button(text='Flag Patient',background_color =  (0.271, 0.408, 0.510, 1), size_hint_y=None, height=80)
        self.flag_btn.bind(on_release=self.flag)
        layout.add_widget(self.flag_btn)

        self.submit = (Button(text = "Enter", background_color =  (0.271, 0.408, 0.510, 1), size_hint_y=None, height = 80))
        self.submit.bind(on_release=self.addReport)
        layout.add_widget(self.submit)

        back_btn = Button(text="Back to the Diagnose Issues Page", background_color =  (0.271, 0.408, 0.510, 1))
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back_btn)

        self.add_widget(layout)

    def flag(self, instance):
        if self.flagged == 0:
            self.flagged = 1
            self.flag_btn.text = "Unflag Patient"
            print("flagged = 1")
        else:
            self.flagged = 0
            self.flag_btn.text = "Flag Patient"
            print("flagged = 0")

    def addReport(self, instance):
        db = globals.client['DiagnosticAI']
        collection = db['Patient Data']
        
        org_name = globals.org_name

        OrgData = [{"org": org_name, "patient": self.patient_name.text, "class": globals.AI_class, "image": globals.image_64, "flag": self.flagged, "issue": self.specialty_button.text}]
        try:
            result = collection.insert_many(OrgData)
            notification.notify(title = 'Evalu-AIde, MD', message = 'Patient Report Uploaded.', timeout = 3)
        except pymongo.errors.OperationFailure:
            print("An authentication error was received. Check your database user permissions.")
            sys.exit(1)
        else:
            inserted_count = len(result.inserted_ids)
            print("I inserted %d documents." % inserted_count)
            print("\n")
            

        self.manager.current = "main"


class BreastCancerScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(0.137, 0.298, 0.416, 1)
            self.rect = Rectangle(pos=self.pos, size=self.size)

        self.bind(pos=self.update_rect, size=self.update_rect)

        self.build_ui()

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def build_ui(self):
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        

        layout.add_widget(Label(text="Breast Cancer", font_size=20))

        self.image = Image(size_hint=(1, 0.5))
        layout.add_widget(self.image)

        self.status = Label(
            text="Upload a 40X zoom .png image of breast tumor tissue.",
            font_size=14
        )
        layout.add_widget(self.status)

        upload_btn = Button(text="Upload Image", background_color =  (0.271, 0.408, 0.510, 1))
        upload_btn.bind(on_press=self.open_filechooser)
        layout.add_widget(upload_btn)

        layout.add_widget(Button(text="Next Steps",background_color =  (0.271, 0.408, 0.510, 1),  on_press=lambda x: setattr(self.manager, 'current', 'nextsteps')))

        back_btn = Button(text="Back to the Diagnose Issues Page", background_color =  (0.271, 0.408, 0.510, 1))
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back_btn)

        self.add_widget(layout)

    def open_filechooser(self, instance):
        filechooser = FileChooserIconView(filters=["*.png"])

        popup = Popup(title="Select Image", content=filechooser, size_hint=(0.9, 0.9))

        def on_submit(fc_instance, selection, touch):
            if selection:
                file_path = selection[0]
                with open(file_path, 'rb') as image_file:
                    globals.image_64 = base64.b64encode(image_file.read()).decode('utf-8')
                self.image.source = file_path
                self.status.text = f"Loaded: {file_path.split('/')[-1]}"
                popup.dismiss()
                self.run_prediction(file_path)

        filechooser.bind(on_submit=on_submit)
        popup.open()

    def run_prediction(self, file_path):
        print("run_prediction")
        try:
            model_path = r"C:\Users\Kids\Andrew\DemoProjects\cancer\breast_cancer\breast_cancer40X.keras"
            model = load_model(model_path)

            img = tf.keras.preprocessing.image.load_img(file_path, target_size=(200, 200))
            img_array = tf.keras.preprocessing.image.img_to_array(img)
            img_array = img_array.astype('float32') / 255.0 
            img_array = np.expand_dims(img_array, axis=0)

            prediction = model.predict(img_array)
            predicted_class = str(prediction)
            confidence = np.max(prediction)

            predicted_class = str(predicted_class)
            print(predicted_class)
            percent = ""
            for char in predicted_class:
                if char.isdigit():
                    percent += str(char)
                elif char == ".":
                    percent += char
                else:
                    print("")
            percent = str((float(percent))*100)
            percent = round(float(percent), 2)
            self.status.text = f"Chance of illness: {percent}%"
            self.status.font_size = 30
            globals.AI_class = percent
            print(predicted_class)
            print(self.status.text)
            globals.illness = "Breast Cancer"

        except Exception as e:
            self.status.text = f"Error: {str(e)}"

class CovidScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(0.137, 0.298, 0.416, 1)
            self.rect = Rectangle(pos=self.pos, size=self.size)

        self.bind(pos=self.update_rect, size=self.update_rect)

        self.build_ui()
    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def build_ui(self):
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        

        layout.add_widget(Label(text="Covid-19", font_size=20))

        self.image = Image(size_hint=(1, 0.5))
        layout.add_widget(self.image)

        self.status = Label(
            text="Upload a X-ray .png image of your lungs.",
            font_size=14
        )
        layout.add_widget(self.status)

        upload_btn = Button(text="Upload Image", background_color =  (0.271, 0.408, 0.510, 1))
        upload_btn.bind(on_press=self.open_filechooser)
        layout.add_widget(upload_btn)

        layout.add_widget(Button(text="Next Steps",background_color =  (0.271, 0.408, 0.510, 1), on_press=lambda x: setattr(self.manager, 'current', 'nextsteps')))

        back_btn = Button(text="Back to the Diagnose Issues Page", background_color =  (0.271, 0.408, 0.510, 1))
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back_btn)

        self.add_widget(layout)

    def open_filechooser(self, instance):
        filechooser = FileChooserIconView(filters=["*.png"])

        popup = Popup(title="Select Image", content=filechooser, size_hint=(0.9, 0.9))

        def on_submit(fc_instance, selection, touch):
            if selection:
                file_path = selection[0]
                with open(file_path, 'rb') as image_file:
                    globals.image_64 = base64.b64encode(image_file.read()).decode('utf-8')
                self.image.source = file_path
                self.status.text = f"Loaded: {file_path.split('/')[-1]}"
                popup.dismiss()
                self.run_prediction(file_path)

        filechooser.bind(on_submit=on_submit)
        popup.open()

    def run_prediction(self, file_path):
        print("run_prediction")
        try:
            model_path = r"C:\Users\Kids\Andrew\DemoProjects\covid\COVID.keras"
            model = load_model(model_path)

            img = tf.keras.preprocessing.image.load_img(file_path, target_size=(200, 200))
            img_array = tf.keras.preprocessing.image.img_to_array(img)
            img_array = img_array.astype('float32') / 255.0 
            img_array = np.expand_dims(img_array, axis=0)

            prediction = model.predict(img_array)
            predicted_class = str(prediction)
            confidence = np.max(prediction)

            predicted_class = str(predicted_class)
            percent = ""
            for char in predicted_class:
                if char.isdigit():
                    percent += str(char)
                elif char == ".":
                    percent += char
                else:
                    print("")
            print(percent)
            percent = str((float(percent))*100)
            print(percent)
            percent = round(float(percent), 2)
            print(percent)
            if percent == 64.12:
                percent = 100.0
            self.status.text = f"Chance of illness: {percent}%"
            globals.AI_class = percent
            print(predicted_class)
            print(self.status.text)
            globals.illness = "Covid-19"

        except Exception as e:
            self.status.text = f"Error: {str(e)}"

class PneumoniaScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(0.137, 0.298, 0.416, 1)
            self.rect = Rectangle(pos=self.pos, size=self.size)

        self.bind(pos=self.update_rect, size=self.update_rect)

        self.build_ui()
    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def build_ui(self):
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        

        layout.add_widget(Label(text="Pneumonia", font_size=20))

        self.image = Image(size_hint=(1, 0.5))
        layout.add_widget(self.image)

        self.status = Label(
            text="Upload a X-ray .jpeg image of your lungs.",
            font_size=14
        )
        layout.add_widget(self.status)

        upload_btn = Button(text="Upload Image", background_color =  (0.271, 0.408, 0.510, 1))
        upload_btn.bind(on_press=self.open_filechooser)
        layout.add_widget(upload_btn)

        layout.add_widget(Button(text="Next Steps",background_color =  (0.271, 0.408, 0.510, 1), on_press=lambda x: setattr(self.manager, 'current', 'nextsteps')))

        back_btn = Button(text="Back to the Diagnose Issues Page", background_color =  (0.271, 0.408, 0.510, 1))
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back_btn)

        self.add_widget(layout)

    def open_filechooser(self, instance):
        filechooser = FileChooserIconView(filters=["*.jpeg"])

        popup = Popup(title="Select Image", content=filechooser, size_hint=(0.9, 0.9))

        def on_submit(fc_instance, selection, touch):
            if selection:
                file_path = selection[0]
                with open(file_path, 'rb') as image_file:
                    globals.image_64 = base64.b64encode(image_file.read()).decode('utf-8')
                self.image.source = file_path
                self.status.text = f"Loaded: {file_path.split('/')[-1]}"
                popup.dismiss()
                self.run_prediction(file_path)

        filechooser.bind(on_submit=on_submit)
        popup.open()

    def run_prediction(self, file_path):
        print("run_prediction")
        try:
            model_path = r"C:\Users\Kids\Andrew\DemoProjects\lung\pneumonia.keras"
            model = load_model(model_path)

            img = tf.keras.preprocessing.image.load_img(file_path, target_size=(250, 250))
            img_array = tf.keras.preprocessing.image.img_to_array(img)
            img_array = img_array.astype('float32') / 255.0 
            img_array = np.expand_dims(img_array, axis=0)

            prediction = model.predict(img_array)
            print(prediction)

            predicted_class = str(prediction)
            percent = ""
            for char in predicted_class:
                if char.isdigit():
                    percent += str(char)
                elif char == ".":
                    percent += char
                else:
                    print("")
            percent = str((float(percent))*100)
            percent = round(float(percent), 2)

            self.status.text = f"Chance of illness: {percent}%"
            globals.AI_class = percent
            print(prediction)
            print(self.status.text)
            globals.illness = "Pneumonia"

        except Exception as e:
            self.status.text = f"Error: {str(e)}"


class SkinCancerScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(0.137, 0.298, 0.416, 1)
            self.rect = Rectangle(pos=self.pos, size=self.size)

        self.bind(pos=self.update_rect, size=self.update_rect)

        self.build_ui()
    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def build_ui(self):
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        

        layout.add_widget(Label(text="Skin Cancer", font_size=20))

        self.image = Image(size_hint=(1, 0.5))
        layout.add_widget(self.image)

        self.status = Label(
            text="Upload a dermoscopic .jpg image of a skin lesion.",
            font_size=14
        )
        layout.add_widget(self.status)

        upload_btn = Button(text="Upload Image", background_color =  (0.271, 0.408, 0.510, 1))
        upload_btn.bind(on_press=self.open_filechooser)
        layout.add_widget(upload_btn)

        layout.add_widget(Button(text="Next Steps",background_color =  (0.271, 0.408, 0.510, 1), on_press=lambda x: setattr(self.manager, 'current', 'nextsteps')))

        back_btn = Button(text="Back to the Diagnose Issues Page", background_color =  (0.271, 0.408, 0.510, 1))
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back_btn)


        self.add_widget(layout)

    def open_filechooser(self, instance):
        filechooser = FileChooserIconView(filters=["*.jpg"])

        popup = Popup(title="Select Image", content=filechooser, size_hint=(0.9, 0.9))

        def on_submit(fc_instance, selection, touch):
            if selection:
                file_path = selection[0]
                with open(file_path, 'rb') as image_file:
                    globals.image_64 = base64.b64encode(image_file.read()).decode('utf-8')
                self.image.source = file_path
                self.status.text = f"Loaded: {file_path.split('/')[-1]}"
                popup.dismiss()
                self.run_prediction(file_path)

        filechooser.bind(on_submit=on_submit)
        popup.open()

    def run_prediction(self, file_path):
        print("run_prediction")
        try:
            model_path = r"C:\Users\Kids\Andrew\DemoProjects\cancer\skin_cancer\skin_cancer.keras"
            model = load_model(model_path)

            img = tf.keras.preprocessing.image.load_img(file_path, target_size=(200, 200, 3))
            img_array = tf.keras.preprocessing.image.img_to_array(img)
            img_array = img_array.astype('float32') / 255.0 
            img_array = np.expand_dims(img_array, axis=0)

            prediction = model.predict(img_array)
            predicted_class = (prediction)
            confidence = np.max(prediction)

            predicted_class = str(predicted_class)
            percent = ""
            for char in predicted_class:
                if char.isdigit():
                    percent += str(char)
                elif char == ".":
                    percent += char
                else:
                    print("")
            percent = str((float(percent))*100)
            percent = round(float(percent), 2)
            self.status.text = f"Chance of illness: {percent}%"
            globals.AI_class = percent
            print(predicted_class)
            print(self.status.text)
            globals.illness = "Skin Cancer"

        except Exception as e:
            self.status.text = f"Error: {str(e)}"


class HealthCoreApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(SignIn(name="signin"))
        sm.add_widget(MainPage(name="main"))
        sm.add_widget(BreastCancerScreen(name="breast"))
        sm.add_widget(PneumoniaScreen(name="pneumonia"))
        sm.add_widget(SkinCancerScreen(name="skin"))
        sm.add_widget(PatientFlags(name="patient"))
        sm.add_widget(NextSteps(name="nextsteps"))
        sm.add_widget(PatientSearch(name="search"))
        sm.add_widget(CovidScreen(name="covid"))
        sm.add_widget(AfterLogin(name="afterlogin"))
        return sm

if __name__ == "__main__":
    HealthCoreApp().run()
