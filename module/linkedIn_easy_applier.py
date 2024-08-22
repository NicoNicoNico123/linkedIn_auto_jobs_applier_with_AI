import base64
import os
import random
import tempfile
import time
import traceback
from datetime import date
from typing import List, Optional, Any, Tuple
import uuid
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait
import tempfile
import time
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate
from datetime import datetime
import io
import time
import pdfkit
import pickle

import utils    

class LinkedInEasyApplier:
    def __init__(self, driver: Any, resume_dir: Optional[str], set_old_answers: List[Tuple[str, str, str]], gpt_answerer: Any):
        if resume_dir is None or not os.path.exists(resume_dir):
            resume_dir = None
        self.driver = driver
        self.resume_dir = resume_dir
        self.set_old_answers = set_old_answers
        self.gpt_answerer = gpt_answerer
        self.current_job = None

    def set_current_job(self, job: Any):
        self.current_job = job
    
    def job_apply(self, job: Any):
        print(f"Starting job application for {job.title} at {job.company}")
        self.set_current_job(job)
        if self.current_job != job:
            print("Error: Failed to set current job correctly")
            raise ValueError("Failed to set current job correctly")
        self.driver.get(job.link)
        time.sleep(random.uniform(3, 5))
        try:
            easy_apply_button = self._find_easy_apply_button()
            job_description = self._get_job_description()
            job.set_job_description(job_description)
            print("Clicking Easy Apply button")
            easy_apply_button.click()
            self.gpt_answerer.set_job(job)
            print("Starting to fill application form")
            self._fill_application_form()
            print("Finished filling application form")
        except Exception:
            tb_str = traceback.format_exc()
            print(f"Exception occurred during job application: {tb_str}")
            self._discard_application()
            raise Exception(f"Failed to apply to job! Original exception: \nTraceback:\n{tb_str}")


    def _find_easy_apply_button(self) -> WebElement:
        buttons = WebDriverWait(self.driver, 10).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, '//button[contains(@class, "jobs-apply-button") and contains(., "Easy Apply")]')
            )
        )
        for index, button in enumerate(buttons):
            try:
                return WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, f'(//button[contains(@class, "jobs-apply-button") and contains(., "Easy Apply")])[{index + 1}]')
                    )
                )
            except Exception as e:
                pass
        raise Exception("No clickable 'Easy Apply' button found")

    def _get_job_description(self) -> str:
        try:
            see_more_button = self.driver.find_element(By.XPATH, '//button[@aria-label="Click to see more description"]')
            see_more_button.click()
            time.sleep(2)
            description = self.driver.find_element(By.CLASS_NAME, 'jobs-description-content__text').text
            self._scroll_page()
            return description
        except NoSuchElementException:
            tb_str = traceback.format_exc()
            raise Exception("Job description 'See more' button not found: \nTraceback:\n{tb_str}")
        except Exception :
            tb_str = traceback.format_exc()
            raise Exception(f"Error getting Job description: \nTraceback:\n{tb_str}")

    def _scroll_page(self) -> None:
        scrollable_element = self.driver.find_element(By.TAG_NAME, 'html')
        utils.scroll_slow(self.driver, scrollable_element, step=300, reverse=False)
        utils.scroll_slow(self.driver, scrollable_element, step=300, reverse=True)

    def _fill_application_form(self):
        print("Entering _fill_application_form method")
        while True:
            print("Calling fill_up method")
            self.fill_up()
            print("Checking for next or submit")
            if self._next_or_submit():
                print("Application submitted or moved to next page")
                break
        print("Exiting _fill_application_form method")

    def _next_or_submit(self):
        next_button = self.driver.find_element(By.CLASS_NAME, "artdeco-button--primary")
        button_text = next_button.text.lower()
        if 'submit application' in button_text:
            self._unfollow_company()
            time.sleep(random.uniform(1.5, 2.5))
            next_button.click()
            time.sleep(random.uniform(1.5, 2.5))
            return True
        time.sleep(random.uniform(1.5, 2.5))
        next_button.click()
        time.sleep(random.uniform(3.0, 5.0))
        self._check_for_errors()


    def _unfollow_company(self) -> None:
        try:
            follow_checkbox = self.driver.find_element(
                By.XPATH, "//label[contains(.,'to stay up to date with their page.')]")
            follow_checkbox.click()
        except Exception as e:
            pass

    def _check_for_errors(self) -> None:
        error_elements = self.driver.find_elements(By.CLASS_NAME, 'artdeco-inline-feedback--error')
        if error_elements:
            raise Exception(f"Failed answering or file upload. {str([e.text for e in error_elements])}")

    def _discard_application(self) -> None:
        try:
            self.driver.find_element(By.CLASS_NAME, 'artdeco-modal__dismiss').click()
            time.sleep(random.uniform(3, 5))
            self.driver.find_elements(By.CLASS_NAME, 'artdeco-modal__confirm-dialog-btn')[0].click()
            time.sleep(random.uniform(3, 5))
        except Exception as e:
            pass

    def fill_up(self) -> None:
        print("Entering fill_up method")
        try:
            easy_apply_content = self.driver.find_element(By.CLASS_NAME, 'jobs-easy-apply-content')
            pb4_elements = easy_apply_content.find_elements(By.CLASS_NAME, 'pb4')
            print(f"Found {len(pb4_elements)} form elements to process")
            for element in pb4_elements:
                print("Processing form element")
                self._process_form_element(element)
        except Exception as e:
            print(f"Exception in fill_up: {str(e)}")
        print("Exiting fill_up method")
        


    def _process_form_element(self, element: WebElement) -> None:
        print("Entering _process_form_element method")
        try:
            if self._is_upload_field(element):
                print("Upload field detected")
                self._handle_upload_fields(element)
            else:
                print("Non-upload field detected")
                self._fill_additional_questions()
        except Exception as e:
            print(f"Exception in _process_form_element: {str(e)}")
        print("Exiting _process_form_element method")

    def _is_upload_field(self, element: WebElement) -> bool:
        try:
            element.find_element(By.XPATH, ".//input[@type='file']")
            return True
        except NoSuchElementException:
            return False

    def _handle_upload_fields(self, element: WebElement) -> None:
        file_upload_elements = self.driver.find_elements(By.XPATH, "//input[@type='file']")
        for element in file_upload_elements:
            parent = element.find_element(By.XPATH, "..")
            self.driver.execute_script("arguments[0].classList.remove('hidden')", element)
            if 'resume' in parent.text.lower():
                if self.resume_dir != None:
                    resume_path = self.resume_dir.resolve()
                if self.resume_dir != None and resume_path.exists() and resume_path.is_file():
                    element.send_keys(str(resume_path))
                else:
                    self._create_and_upload_resume(element)
            elif 'cover' in parent.text.lower():
                self._create_and_upload_cover_letter(element)
    
    def _generate_safe_filename(self, prefix=''):
        if not self.current_job:
            print("Error: No current job set for file generation")
            raise ValueError("No current job set for file generation")

        print(f"Current job: {self.current_job.title} at {self.current_job.company}")

        today_date = datetime.now().strftime("%d%m%Y")

        # Split the title and take only unique parts
        title_parts = self.current_job.title.split()
        unique_title_parts = []
        for part in title_parts:
            if part not in unique_title_parts:
                unique_title_parts.append(part)
        
        safe_title = ''.join(e for e in ' '.join(unique_title_parts) if e.isalnum())
        safe_company = ''.join(e for e in self.current_job.company if e.isalnum())
        
        base_filename = f"{prefix}_{safe_title}_{safe_company}_{today_date}" if prefix else f"{safe_title}_{safe_company}_{today_date}"
        
        print(f"Generated base filename: {base_filename}")
        return base_filename

    def _create_and_upload_resume(self, element):
        print("Starting _create_and_upload_resume method")
        folder_path = 'generated_cv'
        
        print(f"Attempting to create folder: {folder_path}")
        os.makedirs(folder_path, exist_ok=True)
        print(f"Folder created or already exists: {folder_path}")

        base_filename = self._generate_safe_filename()

        max_retries = 3
        retry_delay = 1

        for attempt in range(max_retries):
            try:
                print(f"Attempt {attempt + 1} to create and upload resume")
                html_string = self.gpt_answerer.get_resume_html()
                print("Resume HTML generated")
                
                html_filename = f"{base_filename}.html"
                html_filepath = os.path.join(folder_path, html_filename)
                print(f"HTML filepath: {html_filepath}")

                print("Writing HTML to file")
                with open(html_filepath, 'w', encoding='utf-8') as html_file:
                    html_file.write(html_string)
                print(f"HTML file saved: {html_filepath}")

                pdf_filename = f"{base_filename}.pdf"
                pdf_filepath = os.path.join(folder_path, pdf_filename)
                print(f"PDF filepath: {pdf_filepath}")

                print(f"Converting HTML to PDF: {pdf_filepath}")
                success = utils.html_to_pdf(html_filepath, pdf_filepath)

                if not success:
                    print("Failed to convert HTML to PDF")
                    raise Exception("Failed to convert HTML to PDF")
                
                print(f"Uploading PDF: {pdf_filepath}")
                element.send_keys(os.path.abspath(pdf_filepath))
                print("Resume uploaded successfully")
                return True

            except Exception as e:
                print(f"Error in attempt {attempt + 1}: {str(e)}")
                if attempt < max_retries - 1:
                    print(f"Retrying in {retry_delay} seconds")
                    time.sleep(retry_delay)
                else:
                    tb_str = traceback.format_exc()
                    print(f"Max retries reached. Upload failed: \nTraceback:\n{tb_str}")
                    raise Exception(f"Max retries reached. Upload failed: \nTraceback:\n{tb_str}")

    def _upload_resume(self, element: WebElement) -> None:
        element.send_keys(str(self.resume_dir))

    def _create_and_upload_cover_letter(self, element: WebElement) -> None:
        print("Starting _create_and_upload_cover_letter method")
        folder_path = os.path.join('generated_cv', 'coverletter')
        
        print(f"Attempting to create folder: {folder_path}")
        os.makedirs(folder_path, exist_ok=True)
        print(f"Folder created or already exists: {folder_path}")

        base_filename = self._generate_safe_filename(prefix='CoverLetter')

        # Generate cover letter content
        print("Generating cover letter content")
        cover_letter = self.gpt_answerer.answer_question_textual_wide_range("Write a cover letter")

        # Create the PDF filename
        pdf_filename = f"{base_filename}.pdf"
        pdf_filepath = os.path.join(folder_path, pdf_filename)
        print(f"PDF filepath: {pdf_filepath}")

        # Create the PDF
        doc = SimpleDocTemplate(pdf_filepath, pagesize=letter,
                                rightMargin=72, leftMargin=72,
                                topMargin=72, bottomMargin=18)

        styles = getSampleStyleSheet()
        style = styles["Normal"]

        # Split the cover letter into paragraphs
        paragraphs = [Paragraph(p, style) for p in cover_letter.split('\n\n')]

        # Build the PDF
        print("Building PDF")
        doc.build(paragraphs)

        print(f"Cover letter PDF saved: {pdf_filepath}")

        # Upload the PDF
        print(f"Uploading PDF: {pdf_filepath}")
        element.send_keys(os.path.abspath(pdf_filepath))
        print("Cover letter uploaded successfully")

    def _fill_additional_questions(self) -> None:
        form_sections = self.driver.find_elements(By.CLASS_NAME, 'jobs-easy-apply-form-section__grouping')
        for section in form_sections:
            self._process_question(section)

    def _process_question(self, section: WebElement) -> None:
        if self._handle_terms_of_service(section):
            return
        self._handle_radio_question(section)
        self._handle_textbox_question(section)
        self._handle_date_question(section)
        self._handle_dropdown_question(section)

    def _handle_terms_of_service(self, element: WebElement) -> bool:
        try:
            question = element.find_element(By.CLASS_NAME, 'jobs-easy-apply-form-element')
            checkbox = question.find_element(By.TAG_NAME, 'label')
            question_text = question.text.lower()
            if 'terms of service' in question_text or 'privacy policy' in question_text or 'terms of use' in question_text:
                checkbox.click()
                return True
        except NoSuchElementException:
            pass
        return False

    def _handle_radio_question(self, element: WebElement) -> None:
        try:
            question = element.find_element(By.CLASS_NAME, 'jobs-easy-apply-form-element')
            radios = question.find_elements(By.CLASS_NAME, 'fb-text-selectable__option')
            if not radios:
                return

            question_text = element.text.lower()
            options = [radio.text.lower() for radio in radios]

            answer = self._get_answer_from_set('radio', question_text, options)
            if not answer:
                answer = self.gpt_answerer.answer_question_from_options(question_text, options)

            self._select_radio(radios, answer)
        except Exception:
            pass

    def _handle_textbox_question(self, element: WebElement) -> None:
        try:
            question = element.find_element(By.CLASS_NAME, 'jobs-easy-apply-form-element')
            question_text = question.find_element(By.TAG_NAME, 'label').text.lower()
            text_field = self._find_text_field(question)

            is_numeric = self._is_numeric_field(text_field)
            answer = self._get_answer_from_set('numeric' if is_numeric else 'text', question_text)

            if not answer:
                answer = self.gpt_answerer.answer_question_numeric(question_text) if is_numeric else self.gpt_answerer.answer_question_textual_wide_range(question_text)

            self._enter_text(text_field, answer)
            self._handle_form_errors(element, question_text, answer, text_field)
        except Exception:
            pass

    def _handle_date_question(self, element: WebElement) -> None:
        try:
            date_picker = element.find_element(By.CLASS_NAME, 'artdeco-datepicker__input')
            date_picker.clear()
            date_picker.send_keys(date.today().strftime("%m/%d/%y"))
            time.sleep(3)
            date_picker.send_keys(Keys.RETURN)
            time.sleep(2)
        except Exception:
            pass

    def _handle_dropdown_question(self, element: WebElement) -> None:
        try:
            question = element.find_element(By.CLASS_NAME, 'jobs-easy-apply-form-element')
            question_text = question.find_element(By.TAG_NAME, 'label').text.lower()
            dropdown = question.find_element(By.TAG_NAME, 'select')
            select = Select(dropdown)
            options = [option.text for option in select.options]

            answer = self._get_answer_from_set('dropdown', question_text, options)
            if not answer:
                answer = self.gpt_answerer.answer_question_from_options(question_text, options)

            self._select_dropdown(dropdown, answer)
        except Exception:
            pass

    def _get_answer_from_set(self, question_type: str, question_text: str, options: Optional[List[str]] = None) -> Optional[str]:
        for entry in self.set_old_answers:
            if isinstance(entry, tuple) and len(entry) == 3:
                if entry[0] == question_type and question_text in entry[1].lower():
                    answer = entry[2]
                    return answer if options is None or answer in options else None
        return None

    def _find_text_field(self, question: WebElement) -> WebElement:
        try:
            return question.find_element(By.TAG_NAME, 'input')
        except NoSuchElementException:
            return question.find_element(By.TAG_NAME, 'textarea')

    def _is_numeric_field(self, field: WebElement) -> bool:
        field_type = field.get_attribute('type').lower()
        if 'numeric' in field_type:
            return True
        class_attribute = field.get_attribute("id")
        return class_attribute and 'numeric' in class_attribute

    def _enter_text(self, element: WebElement, text: str) -> None:
        element.clear()
        element.send_keys(text)

    def _select_dropdown(self, element: WebElement, text: str) -> None:
        select = Select(element)
        select.select_by_visible_text(text)

    def _select_radio(self, radios: List[WebElement], answer: str) -> None:
        for radio in radios:
            if answer in radio.text.lower():
                radio.find_element(By.TAG_NAME, 'label').click()
                return
        radios[-1].find_element(By.TAG_NAME, 'label').click()

    def _handle_form_errors(self, element: WebElement, question_text: str, answer: str, text_field: WebElement) -> None:
        try:
            error = element.find_element(By.CLASS_NAME, 'artdeco-inline-feedback--error')
            error_text = error.text.lower()
            new_answer = self.gpt_answerer.try_fix_answer(question_text, answer, error_text)
            self._enter_text(text_field, new_answer)
        except NoSuchElementException:
            pass

    
if __name__ == "__main__":

    def load_job_object(file_path):
        with open(file_path, 'rb') as f:
            return pickle.load(f)

    # Load the Job object from the pickle file
    pickle_file_path = '/app/data_folder/output/success/TerritoryManagerTerritoryManagerwithverification_Consult_20240816_092317.pkl'
    job = load_job_object(pickle_file_path)
    print(f"Loaded job: {job.title} at {job.company}")

    # Create a mock element for testing
    class MockElement:
        def send_keys(self, *args):
            print(f"Mock upload: {args}")

    # Create a mock GPTAnswerer
    class MockGPTAnswerer:
        def get_resume_html(self):
            return "<html><body><h1>Mock Resume</h1></body></html>"

    # Create an instance of LinkedInEasyApplier with mock objects
    easy_applier = LinkedInEasyApplier(None, None, None, MockGPTAnswerer())
    easy_applier.current_job = job  # Set the current job

    # Call the method directly
    easy_applier._create_and_upload_resume(MockElement())