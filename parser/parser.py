import re
import json
import math

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException

def create_chrome_driver():
    """Создает Chrome драйвер с настройками для обхода SSL ошибок"""
    options = Options()
    
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--disable-web-security')
    
    options.add_argument('--disable-javascript')
    options.add_argument('--blink-settings=imagesEnabled=false')
    options.add_argument('--disable-extensions')
    options.add_argument('--no-sandbox')
    
    # Блокировка конкретных медленных доменов
    options.add_argument('--host-resolver-rules=MAP stat.sputnik.ru 127.0.0.1, MAP www.google-analytics.com 127.0.0.1, MAP mc.yandex.ru 127.0.0.1')
    
    driver = webdriver.Chrome(options=options)
    
    return driver

def create_firefox_driver():
    """Создает Chrome драйвер с настройками для обхода SSL ошибок"""
    
    driver = webdriver.Firefox()
    
    return driver

def normalize_date(date_str):
    """Нормализует дату в ISO формат"""
    if not date_str or date_str in ['Не указана', 'Не указано']:
        return None
    
    try:
        month_mapping = {
            'января': '01', 'февраля': '02', 'марта': '03', 'апреля': '04',
            'мая': '05', 'июня': '06', 'июля': '07', 'августа': '08',
            'сентября': '09', 'октября': '10', 'ноября': '11', 'декабря': '12'
        }
        
        if re.match(r'\d{2}\.\d{2}\.\d{4}', date_str):
            day, month, year = date_str.split('.')
            return f"{year}-{month}-{day}"
        
        match = re.search(r'(\d{1,2})\s+(\w+)\s+(\d{4})', date_str)
        if match:
            day, month_ru, year = match.groups()
            month = month_mapping.get(month_ru.lower())
            if month:
                return f"{year}-{month}-{day.zfill(2)}"
                
    except:
        pass
    return date_str

def normalize_participant_name(name):
    """Нормализует название участника с обработкой сложных форматов"""
    if not name or name == 'не указаны':
        return None
    
    org_forms = [
        'ООО', 'ПАО', 'АО', 'ЗАО', 'ИП', 'ФГУП', 'ГУП', 'МУП', 
        'ОАО', 'НКО', 'ТСЖ', 'ПК', 'КФХ', 'ГК', 'МК', 'УП', 'ХП',
    ]
    
    # Паттерны для сложных форматов
    patterns = [
        # Паттерн 1: "Генеральному директору ООО «ФРЕШ РЕСТАРТ» Томилину Д.В."
        (r'^(.*?)\s+({})[\s\"\«]([^\"\»]+)[\"\»]\s+(.*)$'.format('|'.join(org_forms)), 
         lambda m: {
             'raw_name': name,
             'norm_name': m.group(3).strip(),  # "ФРЕШ РЕСТАРТ"
             'org_form': m.group(2),           # "ООО"
             'position': m.group(1).strip(),   # "Генеральному директору"
             'contact_person': m.group(4).strip()  # "Томилину Д.В."
         }),
        
        # Паттерн 2: "ООО «ФРЕШ РЕСТАРТ» (ИНН: 1234567890)"
        (r'^({})[\s\"\«]([^\"\»]+)[\"\»]\s*(?:\([^)]*\))?$'.format('|'.join(org_forms)),
         lambda m: {
             'raw_name': name,
             'norm_name': m.group(2).strip(),
             'org_form': m.group(1)
         }),
        
        # Паттерн 3: "ФРЕШ РЕСТАРТ, ООО"
        (r'^([^,]+),\s*({})$'.format('|'.join(org_forms)),
         lambda m: {
             'raw_name': name,
             'norm_name': m.group(1).strip(),
             'org_form': m.group(2)
         }),
        
        # Паттерн 4: Простая форма "ООО ФРЕШ РЕСТАРТ"
        (r'^({})\s+([^\"\«].*)$'.format('|'.join(org_forms)),
         lambda m: {
             'raw_name': name,
             'norm_name': m.group(2).strip(),
             'org_form': m.group(1)
         }),
        
        # Паттерн 5: Простая форма с кавычками "ООО «ФРЕШ РЕСТАРТ»"
        (r'^({})[\s\"\«]([^\"\»]+)[\"\»]$'.format('|'.join(org_forms)),
         lambda m: {
             'raw_name': name,
             'norm_name': m.group(2).strip(),
             'org_form': m.group(1)
         })
    ]
    
    for form in org_forms:
        if name.startswith(form):
            clean_name = name.replace(form, '').strip()
            clean_name = re.sub(r'^[\"\«\']|[\"\»\']$', '', clean_name).strip()
            return {
                'raw_name': name,
                'norm_name': clean_name,
                'org_form': form
            }
    
    for pattern, handler in patterns:
        match = re.match(pattern, name, re.IGNORECASE)
        if match:
            result = handler(match)
            result['norm_name'] = re.sub(r'\([^)]*\)', '', result['norm_name']).strip()
            return result
    
    # Если ни один паттерн не подошел - возвращаем базовую структуру
    return {
        'raw_name': name,
        'norm_name': name,
        'org_form': None
    }

def normalize_id(raw_id):
    """Нормализует ID дела или документа для удобства работы"""
    if not raw_id:
        return ""
    
    translit_map = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e',
        'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
        'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
        'ф': 'f', 'х': 'h', 'ц': 'c', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch', 'ъ': '',
        'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
        'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E', 'Ё': 'E',
        'Ж': 'Zh', 'З': 'Z', 'И': 'I', 'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M',
        'Н': 'N', 'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T', 'У': 'U',
        'Ф': 'F', 'Х': 'H', 'Ц': 'C', 'Ч': 'Ch', 'Ш': 'Sh', 'Щ': 'Sch', 'Ъ': '',
        'Ы': 'Y', 'Ь': '', 'Э': 'E', 'Ю': 'Yu', 'Я': 'Ya'
    }
    
    # Транслитерация кириллических символов
    normalized = ''.join(translit_map.get(char, char) for char in raw_id)
    
    # Заменяем все не-буквенно-цифровые символы на подчеркивания
    normalized = re.sub(r'[^a-zA-Z0-9\-]', '_', normalized)
    
    # Убираем множественные подчеркивания
    normalized = re.sub(r'_+', '_', normalized)
    
    normalized = normalized.strip('_')
    
    normalized = normalized.lower()
    
    return normalized

def parse_data(driver, start_page=2, last_page=1, step=-1):
    """Функция парсит данные из базы ФАС"""
    
    all_cases_data = {
        'cases': []
    }
    documents = {'documents': []}
    for page in range(start_page, last_page, step):
        driver.get(f"https://br.fas.gov.ru/?page={page}&")    
        
        cases_on_page = driver.find_elements(By.CSS_SELECTOR, "a[href*='/cases/']")
        cases_urls = [case.get_attribute('href') for case in cases_on_page]
        
        for case_url in cases_urls:
            driver.get(case_url)
            
            # Парсим детали дела
            case_details = driver.find_elements(By.CLASS_NAME, "col-sm-12")[4:]
            
            case_name = case_details[0].text
            other_details = case_details[1].text.split('\n')
            
            case_id_match = re.search(r'№([^ ]+)', case_name)
            raw_case_id = case_id_match.group(1) if case_id_match else f"case_{hash(case_name)}"
            case_id = 'fas_' + normalize_id(raw_case_id)
            
            date_match = re.search(r'от (\d{1,2} \w+ \d{4}) г\.', case_name)
            raw_date = date_match.group(1) if date_match else ""
            case_date = normalize_date(raw_date)
            
            case_record = {
                'case_id': case_id,
                'raw_id': raw_case_id,
                'case_name': case_name,
                'case_date': case_date,
                'case_url': case_url,
                'procedure_type': None,
                'registration_date': None, 
                'department': None,
                'activity_sphere': None,
                'initiation_date': None,
                'review_stage': None,
                'closing_date': None,
                'participants': [],
            }
                        
            for detail_name_idx in range(0, len(other_details), 2):
                if detail_name_idx + 1 >= len(other_details):
                    continue
                    
                key = other_details[detail_name_idx]
                value = other_details[detail_name_idx + 1]
                
                if value in ['Не указана', 'Не указано', '']:
                    value = None
                
                field_mapping = {
                    'Процедура': 'procedure_type',
                    'Дата регистрации': 'registration_date',
                    'Управление': 'department', 
                    'Сфера деятельности': 'activity_sphere',
                    'Дата возбуждения': 'initiation_date',
                    'Стадия рассмотрения': 'review_stage',
                    'Дата закрытия': 'closing_date'
                }
        
                if key in field_mapping:
                    # Нормализуем даты
                    if 'дата' in key.lower() and value:
                        value = normalize_date(value)
                    case_record[field_mapping[key]] = value
                    
            # Парсим участников дела
            participants_elements = driver.find_elements(By.CLASS_NAME, "col-sm-10")
            case_record['participants'] = []

            if participants_elements:
                try:
                    participants_text = participants_elements[-2].text.split('\n')

                    for participant_idx in range(1, len(participants_text), 4):
                        if participant_idx + 2 >= len(participants_text):
                            continue
                            
                        participant_name = participants_text[participant_idx]
                        inn_line = participants_text[participant_idx + 1].split()
                        role = participants_text[participant_idx + 2]
                        
                        inn = None
                        ogrn = None
                        
                        if inn_line:
                            inn = inn_line[1]
                            ogrn = inn_line[3]
                        
                        normalized_participant = normalize_participant_name(participant_name)
                        
                        participant_record = {
                            'raw_name': normalized_participant['raw_name'],
                            'norm_name': normalized_participant['norm_name'],
                            'org_form': normalized_participant['org_form'],
                            'inn': inn,
                            'ogrn': ogrn,
                            'role': role
                        }
                        case_record['participants'].append(participant_record)
                        
                except Exception as e:
                    print(f"Ошибка при парсинге участников для дела {case_id}: {e}")
            
            all_cases_data['cases'].append(case_record)
            
            # Парсим связанные документы
            linked_documents = driver.find_elements(By.LINK_TEXT, "перейти >>")
            doc_urls = [doc.get_attribute('href') for doc in linked_documents]
            
            for doc_idx, doc_url in enumerate(doc_urls):
                driver.get(doc_url)
                try:
                    title_elements = driver.find_elements(By.CSS_SELECTOR, ".col-sm-12 h3")
                    title_text = title_elements[1].text if len(title_elements) > 1 else f"Документ_{doc_idx}"
                    
                    doc_id_match = re.search(r'№([^ ]+)', title_text)
                    raw_doc_id = doc_id_match.group(1) if doc_id_match else f"doc_{doc_idx}_{case_id}"
                    
                    doc_id = normalize_id(raw_doc_id)
                    
                    doc_date_match = re.search(r'от (\d{1,2} \w+ \d{4}) г\.', title_text)
                    doc_date_raw = doc_date_match.group(1) if doc_date_match else ""
                    
                    if doc_date_raw:
                        try:
                            doc_date = normalize_date(doc_date_raw)
                        except:
                            doc_date = None
                    else:
                        doc_date = None
                    
                    container = driver.find_element(By.ID, "document_text_container")
                    full_document_text = container.text
                    
                    lines = full_document_text.split('\n')
                    cleaned_lines = []
                    
                    for line in lines:
                        cleaned_line = re.sub(r' +', ' ', line)  # Убираем множественные пробелы
                        cleaned_line = re.sub(r',+', ',', cleaned_line)  # Убираем множественные запятые
                        cleaned_line = cleaned_line.strip()
                        if cleaned_line:
                            cleaned_lines.append(cleaned_line)
                    
                    cleaned_text = '\n'.join(cleaned_lines)
                    
                    text_length = len(cleaned_text)
                    
                    doc_type_element = driver.find_element(By.CSS_SELECTOR, ".container-fluid a[href*='category=']").text
                    
                    if doc_type_element:
                        document_type = doc_type_element
                    else:
                        document_type = "Другое"
                        if "письмо" in title_text.lower():
                            document_type = "Письмо"
                        elif "уведомление" in title_text.lower():
                            document_type = "Уведомление"
                        elif "решение" in title_text.lower():
                            document_type = "Решение"
                        elif "предписание" in title_text.lower():
                            document_type = "Предписание"
                    
                    document_record = {
                        'case_id': case_id,  # Связь с основным делом
                        'document_id': doc_id,
                        'raw_doc_id': raw_doc_id,
                        'title': title_text,
                        'document_date': doc_date,
                        'url': doc_url,
                        'document_text': cleaned_text,
                        'text_length': text_length,
                        'document_type': document_type
                    }
                    
                    documents['documents'].append(document_record)
                    
                except NoSuchElementException as e:
                    documents['documents'].append({
                        'case_id': case_id,
                        'document_id': f"unavailable_{doc_idx}",
                        'raw_doc_id': f"unavailable_{doc_idx}",
                        'title': f"Недоступный документ {doc_idx}",
                        'document_date': "",
                        'url': doc_url,
                        'document_text': "Документ недоступен",
                        'text_length': 0,
                        'document_type': "Недоступен"
                    })
                except Exception as e:
                    continue
            
    return all_cases_data, documents

def parse_pages_count(driver):
    """
    Функция возвращает количество страниц со списками дел на сайте базы решений ФАС
    
    Args:
        driver (webdriver): драйвер с помощью которого осуществляется парсинг
    """
    driver.get('https://br.fas.gov.ru/')
    
    total_element = driver.find_element(By.XPATH, "//span[contains(text(), 'Всего:')]")
    total_text = int(total_element.text.split()[-1])
    
    driver.close()
    return total_text

def parse_count_of_cases_from_first_page(driver):
    """
    Функция возвращает количество дел с первой страницы базы решений ФАС
    
    Args:
        driver (webdriver): драйвер с помощью которого осуществляется парсинг
    """
    driver.get('https://br.fas.gov.ru/')
    
    cases_on_page = driver.find_elements(By.CSS_SELECTOR, "a[href*='/cases/']")
    count_of_cases = len(cases_on_page)

    return count_of_cases

def save_to_json(cases:dict, documents:dict, file_for_cases = 'cases.json', file_for_docs = 'docs.json', mode='w'):
    with open(file=file_for_cases, mode=mode, encoding='utf-8') as data_file:
        json.dump(cases, data_file, ensure_ascii=False, indent=4)
        
    with open(file=file_for_docs, mode=mode, encoding='utf-8') as docs_file:
        json.dump(documents, docs_file, ensure_ascii=False, indent=4)
        
def count_new_pages(pages_count:int, count_of_cases:int, count_of_cases_at_first_page:int):
    """Функция возвращает количество не спарщенных страниц.

    Args:
        pages_count (int): Количество страниц с названиями дел на сайте (на одной странице до 10 дел)
        count_or_cases (int): Количество дел в базе
        count_of_cases_at_first_page:int Количество дел на первой странцице
    """
    COUNT_CASES_AT_LAST_PAGE = 3
    MAX_COUNT_CASES_AT_PAGE = 10
    FIRST_AND_LAST_PAGES = 2
    
    count_new_pages = math.ceil(((pages_count - FIRST_AND_LAST_PAGES) * MAX_COUNT_CASES_AT_PAGE 
                                 + COUNT_CASES_AT_LAST_PAGE + count_of_cases_at_first_page 
                                 - count_of_cases)/10)
    
    return count_new_pages