import re
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.contrib.auth.password_validation import validate_password


# Lista de cuvinte jignitoare în română
PROFANITY_WORDS = [
    # Cuvinte jignitoare comune în română
    'prost', 'proasta', 'prost', 'idiot', 'idiota', 'imbecil', 'imbecila',
    'cretin', 'cretina', 'tâmpit', 'tâmpita', 'fraier', 'fraiera',
    'muist', 'muista', 'pizda', 'pula', 'cacat', 'rahat', 'futut', 'fututa',
    'nenorocit', 'nenorocita', 'jegos', 'jegoasa', 'ordinar', 'ordinara',
    'nesimtit', 'nesimtita', 'javra', 'javra', 'curva', 'curvar',
    'handicapat', 'handicapata', 'retardat', 'retardata', 'debil', 'debila',
    'oligofren', 'oligofrena', 'dement', 'dementa', 'nebun', 'nebuna',
    'schizofrenic', 'schizofrenică', 'psihopat', 'psihopata',
    # Variante cu diacritice
    'tâmpit', 'tâmpită', 'căcat', 'rahat', 'nenorocit', 'nenorocită',
    'jegoasă', 'ordinară', 'nesimțit', 'nesimțită', 'handicapat', 'handicapată',
    'retardat', 'retardată', 'debil', 'debilă', 'oligofren', 'oligofrenă',
    'dement', 'dementă', 'nebun', 'nebună', 'schizofrenic', 'schizofrenic',
    # Injurii regionale
    'boschetar', 'boschetara', 'tigan', 'tiganca', 'jidan', 'jidanca',
    'ungur', 'unguroaica', 'sas', 'sasoaica',
    # Cuvinte în engleză
    'fuck', 'shit', 'bitch', 'asshole', 'damn', 'hell', 'stupid', 'idiot',
    'moron', 'retard', 'gay', 'fag', 'nigger', 'whore', 'slut',
]


def validate_no_profanity(value):
    """
    Validează că textul nu conține cuvinte jignitoare.
    """
    if not value:
        return
    
    # Convertește la lowercase și elimină diacriticele pentru comparație
    clean_value = value.lower()
    
    # Înlocuiește diacriticele cu echivalentele fără diacritice
    diacritics_map = {
        'ă': 'a', 'â': 'a', 'î': 'i', 'ș': 's', 'ț': 't',
        'Ă': 'a', 'Â': 'a', 'Î': 'i', 'Ș': 's', 'Ț': 't'
    }
    
    for diacritic, replacement in diacritics_map.items():
        clean_value = clean_value.replace(diacritic, replacement)
    
    # Verifică fiecare cuvânt jignitor
    for word in PROFANITY_WORDS:
        # Verifică cuvântul exact și variante cu caractere speciale
        pattern = r'\b' + re.escape(word.lower()) + r'\b'
        if re.search(pattern, clean_value):
            raise ValidationError(
                f'Textul conține limbaj nepotrivit. Te rugăm să folosești un limbaj respectuos.'
            )
    
    # Verifică și variante cu caractere speciale (ex: p@ss, sh1t)
    suspicious_patterns = [
        r'p[a@]ss', r'sh[i1]t', r'f[u*]ck', r'b[i1]tch', r'd[a@]mn',
        r'pr[o0]st', r'[i1]d[i1][o0]t', r'[i1]mb[e3]c[i1]l', r'cr[e3]t[i1]n',
        r't[a@]mp[i1]t', r'fra[i1][e3]r', r'mu[i1]st', r'p[i1]zd[a@]',
        r'pul[a@]', r'c[a@]c[a@]t', r'rah[a@]t', r'fut[u*]t',
    ]
    
    for pattern in suspicious_patterns:
        if re.search(pattern, clean_value):
            raise ValidationError(
                f'Textul conține limbaj nepotrivit. Te rugăm să folosești un limbaj respectuos.'
            )


def validate_romanian_phone(value):
    """
    Validează numărul de telefon românesc.
    """
    if not value:
        return
    
    # Elimină spațiile și caracterele speciale
    clean_number = re.sub(r'[\s\-\(\)]', '', value)
    
    # Verifică formatele românești valide
    romanian_patterns = [
        r'^0[2-3]\d{8}$',      # Telefon fix: 021xxxxxxx, 031xxxxxxx
        r'^07[0-9]\d{7}$',     # Mobil: 07xxxxxxxx
        r'^\+407[0-9]\d{7}$',  # Mobil cu prefix: +407xxxxxxxx
        r'^\+40[2-3]\d{8}$',   # Fix cu prefix: +4021xxxxxxx
    ]
    
    is_valid = any(re.match(pattern, clean_number) for pattern in romanian_patterns)
    
    if not is_valid:
        raise ValidationError(
            'Numărul de telefon nu este valid. '
            'Folosește format românesc: 0721234567 sau +40721234567'
        )


def validate_strong_password(password):
    """
    Validează că parola este suficient de puternică.
    """
    if not password:
        raise ValidationError('Parola este obligatorie.')
    
    if len(password) < 8:
        raise ValidationError('Parola trebuie să aibă cel puțin 8 caractere.')
    
    # Verifică că are cel puțin o literă mare
    if not re.search(r'[A-Z]', password):
        raise ValidationError('Parola trebuie să conțină cel puțin o literă mare.')
    
    # Verifică că are cel puțin o literă mică
    if not re.search(r'[a-z]', password):
        raise ValidationError('Parola trebuie să conțină cel puțin o literă mică.')
    
    # Verifică că are cel puțin o cifră
    if not re.search(r'\d', password):
        raise ValidationError('Parola trebuie să conțină cel puțin o cifră.')
    
    # Verifică că nu conține cuvinte comune
    common_passwords = [
        'password', 'parola', '123456', 'qwerty', 'admin', 'user',
        'romania', 'bucuresti', 'iubire', 'familie', 'casa'
    ]
    
    if password.lower() in common_passwords:
        raise ValidationError('Parola este prea comună. Alege o parolă mai sigură.')
    
    # Folosește și validatorul Django implicit
    try:
        validate_password(password)
    except ValidationError as e:
        # Traduce mesajele în română
        romanian_messages = []
        for message in e.messages:
            if 'too common' in message:
                romanian_messages.append('Parola este prea comună.')
            elif 'too short' in message:
                romanian_messages.append('Parola este prea scurtă.')
            elif 'entirely numeric' in message:
                romanian_messages.append('Parola nu poate fi doar cifre.')
            elif 'too similar' in message:
                romanian_messages.append('Parola este prea similară cu informațiile personale.')
            else:
                romanian_messages.append(message)
        
        if romanian_messages:
            raise ValidationError(romanian_messages)


def validate_email_format(email):
    """
    Validează formatul email-ului.
    """
    if not email:
        raise ValidationError('Adresa de email este obligatorie.')
    
    try:
        validate_email(email)
    except ValidationError:
        raise ValidationError('Adresa de email nu este validă.')
    
    # Verifică domenii suspecte
    suspicious_domains = [
        '10minutemail.com', 'tempmail.org', 'guerrillamail.com',
        'mailinator.com', 'throwaway.email', 'temp-mail.org'
    ]
    
    domain = email.split('@')[1].lower() if '@' in email else ''
    if domain in suspicious_domains:
        raise ValidationError('Te rugăm să folosești o adresă de email permanentă.')


def validate_name(name):
    """
    Validează numele (prenume/nume de familie).
    """
    if not name:
        raise ValidationError('Acest câmp este obligatoriu.')
    
    if len(name.strip()) < 2:
        raise ValidationError('Numele trebuie să aibă cel puțin 2 caractere.')
    
    # Verifică că conține doar litere, spații și diacritice românești
    if not re.match(r'^[A-Za-zÀ-ÿĂăÂâÎîȘșȚț\s\-\']+$', name):
        raise ValidationError('Numele poate conține doar litere, spații, cratimă și apostrof.')
    
    # Verifică profanity
    validate_no_profanity(name)


def validate_company_name(name):
    """
    Validează numele companiei.
    """
    if not name:
        return  # Opțional
    
    if len(name.strip()) < 2:
        raise ValidationError('Numele companiei trebuie să aibă cel puțin 2 caractere.')
    
    if len(name) > 200:
        raise ValidationError('Numele companiei este prea lung (maxim 200 caractere).')
    
    # Verifică profanity
    validate_no_profanity(name)


def validate_description(description):
    """
    Validează descrierea.
    """
    if not description:
        return  # Opțional
    
    if len(description.strip()) < 10:
        raise ValidationError('Descrierea trebuie să aibă cel puțin 10 caractere.')
    
    if len(description) > 1000:
        raise ValidationError('Descrierea este prea lungă (maxim 1000 caractere).')
    
    # Verifică profanity
    validate_no_profanity(description)


def validate_services_selection(services):
    """
    Validează selecția de servicii (1-10 servicii).
    """
    if not services:
        raise ValidationError('Trebuie să selectezi cel puțin un serviciu.')

    if len(services) > 10:
        raise ValidationError('Poți selecta maximum 10 servicii.')

    if len(services) < 1:
        raise ValidationError('Trebuie să selectezi cel puțin un serviciu.')


def validate_coverage_radius(radius):
    """
    Validează raza de acoperire (5-150 km).
    """
    if radius < 5:
        raise ValidationError('Raza de acoperire trebuie să fie cel puțin 5 km.')

    if radius > 150:
        raise ValidationError('Raza de acoperire nu poate fi mai mare de 150 km.')


def validate_bio_length(bio):
    """
    Validează că biografia are minim 200 caractere.
    """
    if not bio:
        raise ValidationError('Biografia este obligatorie.')

    clean_bio = bio.strip()
    if len(clean_bio) < 200:
        raise ValidationError(f'Biografia trebuie să aibă cel puțin 200 caractere. Ai scris {len(clean_bio)} caractere.')

    # Verifică profanity
    validate_no_profanity(bio)


def validate_cui_format(cui):
    """
    Validează formatul CUI românesc.
    """
    if not cui:
        return  # Opțional

    # Elimină spațiile și caracterele speciale
    clean_cui = re.sub(r'[^0-9]', '', cui)

    # CUI românesc: 2-10 cifre
    if not re.match(r'^\d{2,10}$', clean_cui):
        raise ValidationError('CUI-ul trebuie să conțină între 2 și 10 cifre.')

    # Verificare cifră de control pentru CUI-uri complete (8+ cifre)
    if len(clean_cui) >= 8:
        # Algoritmul de verificare CUI românesc
        control_key = "753217532"
        if len(clean_cui) == 10:
            # CUI cu 10 cifre
            check_sum = sum(int(clean_cui[i]) * int(control_key[i]) for i in range(9))
            control_digit = check_sum * 10 % 11
            if control_digit == 10:
                control_digit = 0

            if int(clean_cui[9]) != control_digit:
                raise ValidationError('CUI-ul nu este valid (cifra de control incorectă).')


def validate_url_format(url):
    """
    Validează formatul URL-ului.
    """
    if not url:
        return  # Opțional

    # Verifică că URL-ul începe cu http:// sau https://
    if not url.startswith(('http://', 'https://')):
        raise ValidationError('URL-ul trebuie să înceapă cu http:// sau https://')

    # Verifică că nu conține cuvinte jignitoare
    validate_no_profanity(url)


def validate_hourly_rate(rate):
    """
    Validează tariful pe oră.
    """
    if rate is None:
        return  # Opțional

    if rate < 10:
        raise ValidationError('Tariful pe oră trebuie să fie cel puțin 10 lei.')

    if rate > 1000:
        raise ValidationError('Tariful pe oră nu poate fi mai mare de 1000 lei.')


def validate_min_job_value(value):
    """
    Validează valoarea minimă a lucrării.
    """
    if value is None:
        return  # Opțional

    if value < 50:
        raise ValidationError('Valoarea minimă a lucrării trebuie să fie cel puțin 50 lei.')

    if value > 100000:
        raise ValidationError('Valoarea minimă a lucrării nu poate fi mai mare de 100.000 lei.')


def validate_portfolio_image(image):
    """
    Validează imaginea din portofoliu.
    """
    if not image:
        raise ValidationError('Imaginea este obligatorie.')

    # Verifică dimensiunea fișierului (max 5MB)
    if image.size > 5 * 1024 * 1024:
        raise ValidationError('Imaginea nu poate fi mai mare de 5MB.')

    # Verifică tipul fișierului
    allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
    if hasattr(image, 'content_type') and image.content_type not in allowed_types:
        raise ValidationError('Tipul de fișier nu este permis. Folosește JPEG, PNG sau WebP.')


def validate_display_name(name):
    """
    Validează numele afișat.
    """
    if not name:
        raise ValidationError('Numele afișat este obligatoriu.')

    if len(name.strip()) < 2:
        raise ValidationError('Numele afișat trebuie să aibă cel puțin 2 caractere.')

    if len(name) > 100:
        raise ValidationError('Numele afișat nu poate fi mai lung de 100 caractere.')

    # Verifică profanity
    validate_no_profanity(name)
