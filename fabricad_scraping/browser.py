import os
import re
from pathlib import Path
from time import sleep

import browsermobproxy as mob
import undetected_chromedriver as uc
from httpx import get
from selenium.common.exceptions import ElementNotInteractableException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from fabricad_scraping.config import config


class Browser:
    def __init__(self, headless=True):
        self.server = mob.Server(
            config['BROWSERMOB_PROXY_PATH'], options={'port': 8090}
        )
        self.server.start()
        self.proxy = self.server.create_proxy()
        options = Options()
        options.add_argument('--ignore-ssl-errors=yes')
        options.add_argument('--ignore-certificate-errors')
        options.add_argument(f'--proxy-server={self.proxy.proxy}')
        options.add_argument(
            f'--user-data-dir={Path("default_user_data").absolute()}'
        )
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

    def download_course(self, discipline, course, download_folder):
        self.proxy.new_har(
            'https://www.fabricad.online/portal/cursos',
            options={'captureHeaders': True},
        )
        self.driver.get('https://www.fabricad.online/portal/cursos')
        selected = False
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
                        selected = True
                        break
                if selected:
                    break
        for e in range(len(self.find_elements('.list-group-item'))):
            self.driver.refresh()
            group = self.find_elements('.list-group-item')[e]
            group_folder = (
                download_folder / group.text.split('Disponível')[0].strip()
            )
            os.makedirs(group_folder, exist_ok=True)
            self.driver.execute_script('arguments[0].click()', group)
            clicked_lessons = []
            while True:
                click = False
                for lesson in self.find_elements('.list-unstyled li'):
                    if (
                        'openTopic' in lesson.get_attribute('onclick')
                        and lesson not in clicked_lessons
                    ):
                        clicked_lessons.append(lesson)
                        click = True
                        lesson_text = lesson.text.split('Disponível')[
                            0
                        ].strip()
                        while not lesson_text:
                            lesson_text = lesson.text.split('Disponível')[
                                0
                            ].strip()
                        lesson_folder = group_folder / lesson_text
                        self.driver.execute_script(
                            'arguments[0].click()', lesson
                        )
                        os.makedirs(lesson_folder, exist_ok=True)
                if not click:
                    break
                sleep(3)
            already_clicked_videos = []
            for lesson in self.find_elements('.list-unstyled li'):
                if 'openTopic' in lesson.get_attribute('onclick'):
                    for i, video in enumerate(
                        self.find_elements('li', element=lesson)
                    ):
                        video_onclick = video.get_attribute('onclick')
                        if 'openMedia' in video_onclick:
                            if video_onclick in already_clicked_videos:
                                continue
                            already_clicked_videos.append(video_onclick)
                            lesson_text = lesson.text.split('Disponível')[
                                0
                            ].strip()
                            while not lesson_text:
                                lesson_text = lesson.text.split('Disponível')[
                                    0
                                ].strip()
                            lesson_folder = group_folder / lesson_text
                            if video.find_elements(
                                By.CSS_SELECTOR, '.fa-video'
                            ) and f'{lesson_text} - {i + 1}.mp4' not in os.listdir(
                                lesson_folder
                            ):
                                while True:
                                    try:
                                        video.click()
                                        break
                                    except:
                                        continue
                                self.download_page_video(
                                    lesson_folder, lesson_text, i
                                )
                            elif video.find_elements(
                                By.CSS_SELECTOR, '.fa-file'
                            ):
                                while True:
                                    try:
                                        video.click()
                                        break
                                    except:
                                        continue
                                self.download_page_pdf(lesson_folder)

    def download_page_video(self, lesson_folder, lesson_text, index):
        har_data = str(self.proxy.new_har())
        for i in range(30):
            if 'playlist' in har_data:
                break
            har_data = str(self.proxy.new_har())
            sleep(1)
            if i == 29:
                self.driver.execute_script(
                    'arguments[0].click()', self.find_element('#btnClose1')
                )
                return
        m3u8_url = re.findall(
            r'https://svbp-sambavideos\.akamaized\.net/voda/_definst_/.+?playlist\.m3u8',
            har_data,
            re.DOTALL,
        )[0]
        with open(
            f'{lesson_folder / lesson_text} - {index + 1}.m3u8', 'wb'
        ) as f:
            response = get(m3u8_url)
            f.write(response.content)
        os.system(
            f"ffmpeg -y -i '{m3u8_url}' -c copy -bsf:a aac_adtstoasc '{lesson_folder / lesson_text} - {index + 1}.mp4' > /dev/null"
        )
        os.remove(f'{lesson_folder / lesson_text} - {index + 1}.m3u8')
        self.driver.execute_script(
            'arguments[0].click()', self.find_element('#btnClose1')
        )

    def download_page_pdf(self, lesson_folder):
        pdf_filename = self.find_element('#path').get_attribute('value')
        if pdf_filename in os.listdir(lesson_folder):
            sleep(3)
            self.driver.execute_script(
                'arguments[0].click()', self.find_element('#btnClose1')
            )
            return
        while True:
            try:
                self.find_element('#btnDownloadTrilha').click()
                if [
                    f
                    for f in os.listdir(Path.home() / 'Downloads')
                    if pdf_filename == f or 'crdownload' in f
                ]:
                    break
            except ElementNotInteractableException:
                pass
            sleep(5)
        while pdf_filename not in os.listdir(Path.home() / 'Downloads'):
            sleep(1)
        os.rename(
            Path.home() / 'Downloads' / pdf_filename,
            Path(lesson_folder) / pdf_filename,
        )
        self.driver.execute_script(
            'arguments[0].click()', self.find_element('#btnClose1')
        )

    def find_element(self, selector, element=None, wait=10):
        return WebDriverWait(element or self.driver, wait).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
        )

    def find_elements(self, selector, element=None, wait=10):
        return WebDriverWait(element or self.driver, wait).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector))
        )

    def __del__(self):
        self.server.stop()
        self.driver.quit()
