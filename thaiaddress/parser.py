"""
This module provides functions for parsing Thai addresses,
extracting phone numbers, emails, and performing named entity recognition (NER)
on Thai text.
"""
import os.path as op
import re
import joblib
import pandas as pd
from fuzzywuzzy import process
from spacy import displacy
from pythainlp.tokenize import word_tokenize,sent_tokenize
from pythainlp import tokenize
from .utils import (
    preprocess,
    is_stopword,
    clean_location_text,
    isThaiWord,
    merge_tokens,
    merge_labels
)
from Levenshtein import jaro
from pythainlp.util import Trie
from pythainlp.phayathaibert.core import NamedEntityTagger

import logging
logging.getLogger().setLevel(logging.ERROR)

MODULE_PATH = op.dirname(__file__)
CRF_MODEL = joblib.load(op.join(MODULE_PATH, "models", "new_model_synthetic_newmm_25000_addoptional.joblib"))

ADDR_DF = pd.read_csv(
    op.join(MODULE_PATH, "data", "thai_address_data.csv"), dtype={"zipcode": str}
)

PROVINCES = list(ADDR_DF.province.unique())
DISTRICTS = list(ADDR_DF.district.unique())
SUBDISTRICTS = list(ADDR_DF.subdistrict.unique())
DISTRICTS_DICT = ADDR_DF.groupby("province")["district"].apply(list)
SUBDISTRICTS_DICT = ADDR_DF.groupby("province")["subdistrict"].apply(list)
DISTRICTS_POST_DICT = ADDR_DF.groupby("zipcode")["district"].apply(list)
SUBDISTRICTS_POST_DICT = ADDR_DF.groupby("zipcode")["subdistrict"].apply(list)
PROVINCES_POST_DICT = ADDR_DF.groupby("zipcode")["province"].apply(list)

custom_dict = SUBDISTRICTS + DISTRICTS + PROVINCES
custom_dict = Trie(custom_dict)

COLORS = {
    "NAME": "#fbd46d",
    "ADDR": "#ff847c",
    "LOC": "#87d4c5",
    "POST": "#def4f0",
    "PHONE": "#ffbffe",
    "EMAIL": "#91a6b8",
}

def doc2features(doc, i):
    """
    Extract features from a tokenized document for CRF model.

    Parameters:
    doc (list): A list of tuples containing tokens and their POS tags.
    i (int): The index of the token for which features are to be extracted.

    Returns:
    dict: A dictionary containing the features for the specified token.
    """
    word, postag = doc[i]

    features = {
        'word.word': word,
        'word.stopword': is_stopword(word),
        'word.isthai': isThaiWord(word),
        'word.isspace': word.isspace(),
        'postag': postag,
        'word.isdigit()': word.isdigit(),
    }
    if word.isdigit() and len(word) == 5:
        features['word.islen5'] = True

    if i > 0:
        prevword, postag1 = doc[i - 1]
        features['word.prevword'] = prevword
        features['word.previsspace'] = prevword.isspace()
        features['word.previsthai'] = isThaiWord(prevword)
        features['word.prevstopword'] = is_stopword(prevword)
        features['word.prepostag'] = postag1
        features['word.prevwordisdigit'] = prevword.isdigit()
    else:
        features['BOS'] = True  # Special "Beginning of Sequence" tag

    # Features from next word
    if i < len(doc) - 1:
        nextword, postag1 = doc[i + 1]
        features['word.nextword'] = nextword
        features['word.nextisspace'] = nextword.isspace()
        features['word.nextpostag'] = postag1
        features['word.nextisthai'] = isThaiWord(nextword)
        features['word.nextstopword'] = is_stopword(nextword)
        features['word.nextwordisdigit'] = nextword.isdigit()
    else:
        features['EOS'] = True  # Special "End of Sequence" tag

    return features

def extract_features(doc):
    """x
    Extract features from a tokenized document for CRF model.

    Parameters:
    doc (list): A list of tuples containing tokens and their POS tags.

    Returns:
    list: A list of dictionaries, where each dictionary contains the features for a token.
    """
    return [doc2features(doc, i) for i in range(len(doc))]

def get_labels(doc):
    """
    Extract labels from a tokenized document.

    Parameters:
    doc (list): A list of tuples containing tokens, POS tags, and labels.

    Returns:
    list: A list of labels corresponding to the tokens in the document.
    """
    return [tag for (token, postag, tag) in doc]

def extract_location(text, option="province", province=None, postal_code=None):
    """
    Extract Thai province, district, or subdistrict from a given text.

    Parameters:
    text (str): Input Thai text that contains location.
    option (str): The type of location to extract ('province', 'district', or 'subdistrict').
    province (str or None): If provided, search for districts and subdistricts within the given province.
    postal_code (str or None): If provided, search for districts and subdistricts within the given postal code.

    Returns:
    str: The extracted location that best matches the input text.
    """
    # preprocess the text
    text = text.replace("\n-", " ")
    text = text.replace("\n", " ")

    if option == "province":
        text = text.split("จ.")[-1].split("จังหวัด")[-1]
        list_check = PROVINCES
        text = text.split()
        word = [word for word in text if word in list_check]
        word = ' '.join(word)

    elif option == "district":
        text = text.split("อ.")[-1].split("อำเภอ")[-1]
        text = text.split(" เขต")[-1]
        list_check = DISTRICTS
        text = text.split()
        word = [word for word in text if word in list_check]
        word = ' '.join(word)

    elif option == "subdistrict":
        text = text.split("ต.")[-1].split("อ.")[0].split("อำเภอ")[0]
        text = text.split(" แขวง")[-1].split(" เขต")[0]
        list_check = SUBDISTRICTS
        text = text.split()
        word = [word for word in text if word in list_check]
        word = ' '.join(word)

    location = ""
    if postal_code is not None and SUBDISTRICTS_POST_DICT.get(postal_code) is not None:
        options_map = {
            "province": PROVINCES,
            "district": DISTRICTS_POST_DICT.get(postal_code, DISTRICTS),
            "subdistrict": SUBDISTRICTS_POST_DICT.get(postal_code, SUBDISTRICTS),
        }
    elif province is not None:
        districts = []
        for d in DISTRICTS_DICT.get(province, DISTRICTS):
            if d != "พระนครศรีอยุธยา":
                districts.append(d.replace(province, ""))
            else:
                districts.append(d)
        options_map = {
            "province": PROVINCES,
            "district": districts,
            "subdistrict": SUBDISTRICTS_DICT.get(province, SUBDISTRICTS),
        }
    else:
        options_map = {
            "province": PROVINCES,
            "district": DISTRICTS,
            "subdistrict": SUBDISTRICTS,
        }
    options = options_map.get(option)

    try:
        locs = [l for l, _ in process.extract(word, options, limit=3)]
        locs.sort(key=len, reverse=False)  # sort from short to long string
        for loc in locs:
            if loc in word:
                location = loc
        if location == "" or location == "เมือง":
            location = [l for l, _ in process.extract(word, options, limit=3)][0]
    except:
        pass
    return location

def find_postal_code(subdistrict=None, district=None, province=None):
    query = {}
    if subdistrict:
        query["subdistrict"] = subdistrict
    if district:
        query["district"] = district
    if province:
        query["province"] = province
    
    result = ADDR_DF.loc[(ADDR_DF[list(query)] == pd.Series(query)).all(axis=1), "zipcode"]
    
    if not result.empty:
        return result.iloc[0]
    else:
        return "-"

def tokens_to_features(tokens, i):
   """
   Convert a list of tokens to a dictionary of features for a specific token index.

   Parameters:
   tokens (list): A list of tuples containing tokens and their labels.
   i (int): The index of the token for which features are to be extracted.

   Returns:
   dict: A dictionary containing the features for the specified token.
   """
   if len(tokens[i]) == 2:
       word, _ = tokens[i]  # unpack word and class
   else:
       word = tokens[i]

   # Features from current word
   features = {
       "bias": 1.0,
       "word.word": word,
       "word[:3]": word[:3],
       "word.isspace()": word.isspace(),
       "word.is_stopword()": is_stopword(word),
       "word.isdigit()": word.isdigit(),
   }
   if word.strip().isdigit() and len(word) == 5:
       features["word.islen5"] = True

   # Features from previous word
   if i > 0:
       prevword = tokens[i - 1][0]
       features.update(
           {
               "-1.word.prevword": prevword,
               "-1.word.isspace()": prevword.isspace(),
               "-1.word.is_stopword()": is_stopword(prevword),
               "-1.word.isdigit()": prevword.isdigit(),
           }
       )
   else:
       features["BOS"] = True  # Special "Beginning of Sequence" tag

   # Features from next word
   if i < len(tokens) - 1:
       nextword = tokens[i + 1][0]
       features.update(
           {
               "+1.word.nextword": nextword,
               "+1.word.isspace()": nextword.isspace(),
               "+1.word.is_stopword()": is_stopword(nextword),
               "+1.word.isdigit()": nextword.isdigit(),
           }
       )
   else:
       features["EOS"] = True  # Special "End of Sequence" tag

   return features


def extract_phone_numbers(text):
    """
    Extract phone numbers from text using regular expressions.

    Parameters:
    text (str): The input text from which to extract phone numbers.

    Returns:
    list or str: The list of extracted phone numbers, or a single phone number if only one is found, or an empty string if none are found.
    """
    text = re.sub(r'\+66\s?', '0', text)
    # Updated pattern to match phone numbers with any non-digit separators
    phone_number_pattern = r'\b0\d{1,2}\D?\d{3}\D?\d{3,4}\b'

    matches = re.findall(phone_number_pattern, text)

    phone_numbers = []
    for phone_number in matches:
        cleaned_number = re.sub(r'\D', '', phone_number)  # Remove all non-digit characters
        if cleaned_number.startswith("02"):
            phone_numbers.append(cleaned_number[:9])  # Keep 9 digits for numbers starting with 02
        else:
            phone_numbers.append(cleaned_number[:10])  # Keep 10 digits for other numbers

    if len(phone_numbers) == 1:
        return phone_numbers[0]
    elif len(phone_numbers) > 1:
        return phone_numbers
    else:
        return "-"



def extract_emails(text):
    """
    Extract email addresses from text using regular expressions.

    Parameters:
    text (str): The input text from which to extract email addresses.

    Returns:
    str or list: The first extracted email address if only one is found, or a list of 
    extracted email addresses if more than one is found, or an empty string if no email addresses are found.
    """
    emails = re.findall(r"\b[\w\.-]+?@\w+?\.\w+?\b", text)
    if len(emails) == 1:
        return emails[0]
    elif len(emails) > 1:
        return emails
    else:
        return "-"


def extract_postal_code(text):
    """
    Extract postal codes from text using regular expressions.

    Parameters:
    text (str): The input text from which to extract postal codes.

    Returns:
    str or None: The extracted postal code if found, otherwise None.
    """
    postal_code_pattern = r'(?<!\d)\d{5}(?!\d)'  # Match 5-digit postal codes not surrounded by digits
    postal_code_matches = re.findall(postal_code_pattern, text)
 
    if postal_code_matches:
        return postal_code_matches[0]
    else:
        return "-"

def correct_location_name(misspelled_word, correct_words, threshold=0.6):
   """
   Correct a misspelled location name by finding the closest match in a list of correct words.

   Parameters:
   misspelled_word (str): The misspelled word to be corrected.
   correct_words (list): A list of correct words to compare against.
   threshold (float): The minimum similarity threshold for considering a match (default: 0.6).

   Returns:
   str: The corrected word if a match is found, otherwise the original misspelled word.
   """
   closest_match = max(correct_words, key=lambda word: jaro(misspelled_word, word))
   return closest_match if jaro(misspelled_word, closest_match) >= threshold else misspelled_word


def get_postal_code(subdistrict, province):
    result = ADDR_DF[(ADDR_DF['subdistrict'] == subdistrict) & (ADDR_DF['province'] == province)]
    if len(result) > 0:
        return result['zipcode'].values[0]
    else:
        return ""

def find_best_subdistrict_and_district(token, subdistrict_and_district_sorted):
    best_subdistrict_and_district = None
    best_subdistrict_and_district_similarity = 0
    
    # Iterate through sorted subdistrict_and_districts to find the best match for this token
    for subdistrict_and_district_candidate in subdistrict_and_district_sorted:
        similarity = jaro(token, subdistrict_and_district_candidate)
        if similarity >= 0.8 and similarity > best_subdistrict_and_district_similarity:
            best_subdistrict_and_district_similarity = similarity
            best_subdistrict_and_district = subdistrict_and_district_candidate
    
    return best_subdistrict_and_district


def check_phone_numbers(dash_count, phone_numbers):
    if dash_count >= 4:
        return phone_numbers if phone_numbers is not None else None
    else:
        return None

def filter_only_address(address, phone_numbers, subdistrict, district, province,postal_code):
    # Convert phone_numbers, subdistrict, district, province to strings if they are not already
    phone_numbers_str = str(phone_numbers)
    subdistrict_str = str(subdistrict)
    district_str = str(district)
    province_str = str(province)
    postal_code_str = str(postal_code)

    
    # Create a combined regex pattern to match any of the unwanted text
    patterns_to_remove = [phone_numbers_str, subdistrict_str, district_str, province_str,postal_code_str,"เมือง"]
    combined_pattern = '|'.join(map(re.escape, patterns_to_remove))
    
    # Remove unwanted patterns from the address
    cleaned_address = re.sub(combined_pattern, '', address)
    
    # Return the cleaned address
    return cleaned_address.strip()

def extract_address(text):
    if len(text) > 300:
        text_list = sent_tokenize(text, engine="crfcut")
        keywords = ["บ้าน", "บริษัท", "เลขที่", "/", "ที่อยู่", "บ้านเลขที่", "หมู่", "ซอย", "หมู่บ้าน", "ถนน", "ตำบล", "แขวง", "ที่ทำการ", "แยก", "ตรอก", "โรงแรม"]
        filtered_text_list = [sentence for sentence in text_list if any(keyword in sentence for keyword in keywords)]
        new_text = max(filtered_text_list, key=len) if filtered_text_list else ""
        if "กรุงเทพมหานคร" in text:
            new_text = new_text.replace("อำเภอ", "เขต").replace("ตำบล", "แขวง")
    else:
        new_text = preprocess(text)
    
    return new_text

def display_entities(tokens: list, labels: list):
    """
    Display tokens and labels

    References
    ----------
    Spacy, https://spacy.io/usage/visualizers
    """
    options = {"ents": list(COLORS.keys()), "colors": COLORS}

    ents = []
    text = ""
    s = 0
    for token, label in zip(tokens, labels):
        text += token
        if label != "O":
            ents.append({"start": s, "end": s + len(token), "label": label})
        s += len(token)

    text_display = {"text": text, "ents": ents, "title": None}
    displacy.render(
        text_display, style="ent", options=options, manual=True, jupyter=True
    )

def parse(text=None, display:bool=False, tokenize_engine="newmm"):
    """
    Parse a given address text and extract phone numbers and emails

    Parameters
    ----------
    text: str, input Thai address text to be parsed
    display: bool, if True, display parsed output
    tokenize_engine: str, pythainlp tokenization engine, default is newmm-safe

    Output
    ------
    address: dict, parsed output
    """

    if not text or text.isspace():  # Handling None, empty string, and string with only spaces
        return None

    detected_address = extract_address(text)
    new_text = preprocess(text)
    # new_text = text

    tokens = word_tokenize(detected_address, engine=tokenize_engine, custom_dict=custom_dict)
    try:
        features = [tokens_to_features(tokens, i) for i in range(len(tokens))]
    except IndexError as e:
        features = []
    preds = CRF_MODEL.predict([features])[0]

    phone_numbers = extract_phone_numbers(new_text.replace('-', ''))
    email_addresses = extract_emails(new_text)

    preds_ = list(zip(tokens, preds))

    address = "".join([token for token, c in preds_ if c == "ADDR"]).strip()
    location = " ".join([token for token, c in preds_ if c == "LOC"]).strip()
    if len(location.split()) <= 4:
        location = ""

    postal_code = extract_postal_code(new_text)
    postal_list = postal_code.split(';')
    unique_postal_list = list(set(postal_list))
    unique_postal = ';'.join(unique_postal_list)

    if unique_postal is not None:
        if unique_postal not in PROVINCES_POST_DICT:
            unique_postal = "-"

    subdistrict = None
    district = None
    province = None
    print(address)
    len_provinces_subdistricts_districts = len([word for word in tokens if word in PROVINCES + SUBDISTRICTS + DISTRICTS])
    print(len_provinces_subdistricts_districts)
    if unique_postal != "-":
        len_provinces_subdistricts_districts += 1
    if (len_provinces_subdistricts_districts >= 2 or sum(word in ['อำเภอ', 'ตำบล', 'จังหวัด', 'เขต', 'แขวง','เเขวง'] for word in tokens) >= 2):
        print(new_text)
        if unique_postal != "-" and unique_postal in PROVINCES_POST_DICT:
            province = PROVINCES_POST_DICT[unique_postal][0]
        elif "จังหวัด" in new_text:
            province_name_split = [part for part in new_text.split("จังหวัด") if part.strip()]
            if len(province_name_split) > 1:
                province_name = province_name_split[-1].split()[0]
                province = province_name
            else:
                province = "-"
        else:
            province = extract_location(location, option="province")

        if "อำเภอ" in new_text:
            district_name = new_text.split("อำเภอ")[-1].split()[0]
            district = district_name
            if district == 'เมือง':
                district = extract_location(location, option="district", province=province)
        elif "เขต" in new_text:
            district_name = new_text.split("เขต")[-1].split()[0]
            district = district_name
        elif district is None and unique_postal != "-" and unique_postal in DISTRICTS_POST_DICT:
            districts_sorted = sorted(DISTRICTS_POST_DICT[unique_postal], key=len, reverse=True)
            district = "-"
            for token in tokens:
                best_district = find_best_subdistrict_and_district(token, districts_sorted)
                if best_district:
                    district = best_district
                    break
        else:
            district = '-'

        if "ตำบล" in new_text:
            subdistrict_name = new_text.split("ตำบล")[-1].split()[0]
            subdistrict = subdistrict_name
        elif subdistrict is None and "เขวง" in new_text:  # Check for "เขวง" instead of "เเขวง"
            subdistrict_name = new_text.split("เขวง")[-1].split()[0]
            subdistrict = subdistrict_name
        elif subdistrict is None and "แขวง" in new_text:  # Check for "แขวง"
            subdistrict_name = new_text.split("แขวง")[-1].split()[0]
            subdistrict = subdistrict_name
        elif subdistrict is None and unique_postal != "-" and unique_postal in SUBDISTRICTS_POST_DICT:
            subdistricts_sorted = sorted(SUBDISTRICTS_POST_DICT[unique_postal], key=len, reverse=True)
            subdistrict = "-"
            for token in tokens:
                best_subdistrict = find_best_subdistrict_and_district(token, subdistricts_sorted)
                if best_subdistrict:
                    subdistrict = best_subdistrict
                    break
        else:
            subdistrict = "-"

        if unique_postal != "-":
            province = correct_location_name(province, PROVINCES)
            subdistrict = correct_location_name(subdistrict, SUBDISTRICTS_POST_DICT[unique_postal])
            if district == 'เมือง':
                district = 'เมือง' + province
            else:
                district = correct_location_name(district, DISTRICTS_POST_DICT[unique_postal])
        else:
            unique_postal = find_postal_code(subdistrict,district,province)
            province = correct_location_name(province, PROVINCES)
            subdistrict = correct_location_name(subdistrict, SUBDISTRICTS)
            if district == 'เมือง':
                district = 'เมือง' + province
            else:
                district = correct_location_name(district, DISTRICTS)

        patterns = ['เขต', 'เเขวง', 'จังหวัด', 'แขวง', 'ตำบล', 'อำเภอ']
    
        patterns.extend([subdistrict, district, province, unique_postal])

        if isinstance(phone_numbers, list):
            patterns.extend(phone_numbers)
        else:
            patterns.append(phone_numbers)

        if isinstance(email_addresses, list):
            patterns.extend(email_addresses)
        else:
            patterns.append(email_addresses)

        clean_address = (clean_location_text(address))
        subdistrict = clean_location_text(str(subdistrict))
        province = clean_location_text(str(province))
        clean_address = filter_only_address(clean_address, phone_numbers, subdistrict, district, province,postal_code)
        dash_count = sum(1 for field in [subdistrict, district, province, phone_numbers, email_addresses, unique_postal] if field == '-')
        if display:
            merge, labels = merge_labels(preds)
            tokens = merge_tokens(tokens, merge)
            display_entities(tokens, labels)
        if dash_count >= 4:
            return None
        else:
            return {
                "text": text,
                "address": clean_address,
                "subdistrict": subdistrict,
                "district": district,
                "province": province,
                "postal_code": unique_postal,
                "phone": phone_numbers,
                "email": email_addresses,
            }
    else:
        if phone_numbers != '-':
            return {"phone": phone_numbers}
        else:
            return None




