import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from fabricad_scraping.config import config


class Browser:
    def __init__(self, headless=True):
        options = Options()
        options.add_argument('--incognito')
        self.driver = uc.Chrome(
            headless=headless, use_subprocess=False, options=options
        )

    def make_login(self):
        self.driver.get('https://www.fabricad.online/portal/login')
        self.find_element('#login').send_keys(config['LOGIN'])
        self.find_element('input[name="senha"]').send_keys(config['PASSWORD'])
        self.find_element('#recaptchav3').click()

    def get_disciplines(self):
        self.driver.get('https://www.fabricad.online/portal/cursos')
        return [e.text for e in self.find_elements('.box-item h6')]

    def get_courses(self, discipline):
        self.driver.get('https://www.fabricad.online/portal/cursos')
        for discipline_element in self.find_elements('.box-item'):
            if (
                self.find_element('h6', element=discipline_element).text
                == discipline
            ):
                discipline_element.click()
                return [
                    e.text for e in self.find_elements('.box-item-package h6')
                ]

    def download_course(self, discipline, course):
        self.driver.get('https://www.fabricad.online/portal/cursos')
        for discipline_element in self.find_elements('.box-item'):
            if (
                self.find_element('h6', element=discipline_element).text
                == discipline
            ):
                discipline_element.click()
                for course_element in self.find_elements('.box-item-package'):
                    if (
                        self.find_element('h6', element=course_element).text
                        == course
                    ):
                        course_element.click()
        breakpoint()

    def find_element(self, selector, element=None, wait=10):
        return WebDriverWait(element or self.driver, wait).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
        )

    def find_elements(self, selector, element=None, wait=10):
        return WebDriverWait(element or self.driver, wait).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector))
        )
