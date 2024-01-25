from fastapi import FastAPI
import random
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup
import math
#from multichat.asgi import application
#python -m uvicorn main:app --reload

def correctDomainExtension(domain: str):
    domain = domain.lower()
    if(domain != 'fr'):        
        match domain:
            case 'uk':
                domain = 'co.uk'
            case 'br':
                domain = 'com.br'
            case 'ar':
                domain = 'com.ar'
            case 'in':
                domain = 'co.in'
            case 'id':
                domain = 'co.id'
            case 'kr':
                domain = 'co.kr'
            case 'za':
                domain = 'co.za'
            case 'tr':
                domain = 'com.tr'
    return domain

app = FastAPI()
@app.get("/")
def accueil():
    return {"Message": "Bienvenue dans l'API de scraping TRANSFERMARKT"}


@app.get("/searchPlayer/{language}_{name}")
def generer_nombre(language: str, name: str):
    """
    Cette fonction donne le résultat de recherche des joueurs masculins existants sur TransfertMarkt sur la première page en fonction de la langue et du nom du joueur renseignés. La langue doit être les 2 lettres de l'extension de domaine associée, et l'ID doit être sous forme numérique.
    """ 
    language = correctDomainExtension(language)
    domain = 'https://www.transfermarkt.' + language     
    url = domain + '/schnellsuche/ergebnis/schnellsuche?query=' + name.lower()
    #Camouflage de l'API
    userAgent = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0'
    headers = {'Content-Type': 'text/html', 'user-agent': str(userAgent)}
    response = requests.get(url, headers=headers)

    playersLists = []
    
    if response.ok:
        soup = BeautifulSoup(response.text, "lxml")
        #Nombre de tableaux principaux
        bigRowsWithLinesList = soup.findAll('div', {'class' : 'large-12 columns'})
        #Envoi d'aucun joueur si la recherche n'aboutit à rien en fonction de l'entête du tableau
        tableTitle = bigRowsWithLinesList[0].find('h2', {'class' : 'content-box-headline'}).text
        match language:
            case 'fr':
                tableTitle = " joueurs" 
            case 'co.uk' | 'us' | 'co.in' | 'co.kr'|'co.za' | 'com':
                tableTitle = " players" 
            case 'es' | 'com.ar' | 'co' | 'mx' | 'pe':
                tableTitle = " jugador" 
            case 'de' | 'at' | 'ch':
                tableTitle = " spielern" 
            case 'it':
                tableTitle = " giocatori" 
            case 'ro':
                tableTitle = " jucători" 
            case 'gr':
                tableTitle = "παικτών" 
            case 'com.br' | 'pt':
                tableTitle = " jogador" 
            case 'co.id':
                tableTitle = " pemain" 
            case 'com.tr':
                tableTitle = " oyunculara" 
            case 'be' | 'nl':
                tableTitle = " spelers " 
            case 'pl':
                tableTitle = "Wyniki wyszukiwania" 
            case 'jp':
                tableTitle = "選手検索結果" 
        if tableTitle not in tableTitle: 
            return { 'players' : 'No players found' }
        oddLines = bigRowsWithLinesList[0].findAll('tr', {'class' : 'odd'})
        evenLines = bigRowsWithLinesList[0].findAll('tr', {'class' : 'even'})
        #Calcul de nombre de ligne à analyser sachant que les index sont alternés
        nbLines = len(oddLines) + len(evenLines)
        rangeLines = math.trunc(nbLines/2)
        oddNumber = False
        if nbLines % 2 == 1:
            rangeLines += 1
            oddNumber = True
        for index in range(rangeLines):
            print(str(index) + ' ' + str(rangeLines))
            #Alternance entre la ligne de class Odd et celle de classe Even
            for oddOrEven in range(2):
                if oddOrEven == 0 :
                    lines = oddLines
                else:
                    if (oddNumber == True) and (index == rangeLines - 1):
                        break
                    else: 
                        lines = evenLines
                linkOnGoing = lines[index].find('td', {'class' : 'hauptlink'}).find('a')['href']
                #Séparation du nom et du prénom
                fullName = lines[index].find('td', {'class' : 'hauptlink'}).text
                listName = fullName.split(" ")
                #Liste des TD dont les valeurs de texte correspondent ensuite à chaque case
                tdList = lines[index].findAll('td')
                #Savoir si joueur à la retraite en fonction de l'image du club
                if tdList[5].find('img')['src'] == "https://tmssl.akamaized.net/images/wappen/tiny/123.png?lm=1456997286":
                    careerEnded = True
                else:
                    careerEnded = False
                #Séparation des nationalités dans une liste
                citizenshipList =[]
                imgCitizenshipList = tdList[7].findAll('img')
                for element in imgCitizenshipList:
                    citizenshipList.append(element['title'])
                #Définition du club ou null si retraité
                if careerEnded == 1 :
                    club = None
                else:
                    club = tdList[5].find('img')['title']
                #Création du json joueur
                playersLists.append({
                    'transferMarktId' : linkOnGoing.split('/')[4],
                    'url' : domain + linkOnGoing,
                    'name' : listName[len(listName)-1],
                    'fullName' : fullName,
                    'imageURL' : lines[index].find('img')['src'],  
                    'age' : tdList[6].text,  
                    'citizenship' : citizenshipList,
                    'isRetired' : careerEnded,
                    'position' : tdList[4].text,
                    'club' : club,
                    'marketValue' : tdList[8].text,
                    'agent' :  tdList[9].text
                })
            
        playerOnGoingJson = { 'players' : playersLists }
        return playerOnGoingJson



@app.get("/searchClub/{language}_{name}")
def searchClub(language: str, name: str):
    """
   Cette fonction donne le résultat de recherche des clubs existants sur TransfertMarkt sur la première page en fonction de la langue et du nom du club renseignés. La langue doit être les 2 lettres de l'extension de domaine associée.
    """ 
    language = correctDomainExtension(language)
    domain = 'https://www.transfermarkt.' + language      
    url = domain + '/schnellsuche/ergebnis/schnellsuche?query=' + name.lower()
    #Brouillage des requêtes
    userAgent = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0'
    headers = {'Content-Type': 'text/html', 'user-agent': str(userAgent)}
    response = requests.get(url, headers=headers)
    clubsList = []    
    if response.ok:
        soup = BeautifulSoup(response.text, "lxml")
        #Nombre de tableaux principaux
        bigRowsWithLinesList = soup.findAll('div', {'class' : 'large-12 columns'})
        #Envoi d'aucun joueur si la recherche n'aboutit à rien en fonction de l'entête du tableau
        clubsTableIndex = 0
        nbOfTables = len(bigRowsWithLinesList)
        for index in range(nbOfTables):
            tableTitle = bigRowsWithLinesList[index].find('h2', {'class' : 'content-box-headline'}).text
            match language:
                case 'fr':
                    tableTitle = "Résultats de recherche: clubs" 
                case 'co.uk' | 'us' | 'co.in' | 'co.kr'|'co.za' | 'com':
                    tableTitle = "Search results: Clubs" 
                case 'es' | 'com.ar' | 'co' | 'mx' | 'pe':
                    tableTitle = "Buscar resultados: Clubes" 
                case 'de' | 'at' | 'ch':
                    tableTitle = "Suchergebnisse zu Vereinen" 
                case 'it':
                    tableTitle = "Risultati società" 
                case 'ro':
                    tableTitle = "Rezultatele căutării: Cluburi" 
                case 'gr':
                    tableTitle = "Αποτελέσματα αναζήτησης ομάδων" 
                case 'com.br' | 'pt':
                    tableTitle = "Resultados da pesquisa para Clubes" 
                case 'co.id':
                    tableTitle = "Hasil pencarian: Klub" 
                case 'com.tr':
                    tableTitle = "Arama sonuçları: Kulüpler"
                case 'be' | 'nl':
                    tableTitle = "Clubs"
                case 'pl':
                    tableTitle = "Lista drużyn"
                case 'jp':
                    tableTitle = "検索結果: クラブ"
            if tableTitle not in tableTitle: 
                if index == nbOfTables - 1 :
                    return { 'clubs' : 'No clubs found' }
            else :
                clubsTableIndex = index
                break
        oddLines = bigRowsWithLinesList[clubsTableIndex].findAll('tr', {'class' : 'odd'})
        evenLines = bigRowsWithLinesList[clubsTableIndex].findAll('tr', {'class' : 'even'})
        #Calcul de nombre de ligne à analyser sachant que les index sont alternés
        nbLines = len(oddLines) + len(evenLines)
        rangeLines = math.trunc(nbLines/2)
        oddNumber = False
        if nbLines % 2 == 1:
            rangeLines += 1
            oddNumber = True
        for index in range(rangeLines):
            print(str(index) + ' ' + str(rangeLines))
            #Alternance entre la ligne de class Odd et celle de classe Even
            for oddOrEven in range(2):
                if oddOrEven == 0 :
                    lines = oddLines
                else:
                    if (oddNumber == True) and (index == rangeLines - 1):
                        break 
                    else: 
                        lines = evenLines
                linkOnGoing = lines[index].find('td', {'class' : 'hauptlink'}).find('a')['href']
                #Liste des TD dont les valeurs de texte correspondent ensuite à chaque case
                tdList = lines[index].findAll('td')
                #Création du json joueur
                clubsList.append({
                    'transferMarktId' : linkOnGoing.split('/')[4],
                    'url' : domain + linkOnGoing,
                    'imageURL' : lines[index].find('img')['src'],
                    'name' : lines[index].find('td', {'class' : 'hauptlink'}).text,
                    'leagueName' : tdList[3].text,
                    'country' : tdList[4].find('img')['title'],
                    'staff' : tdList[5].text,
                    'marketValue' : tdList[6].text,
                    'stadiumName' : tdList[8].find('a')['title']
                })            
        return { 'clubs' : clubsList }
                

@app.get("/getPlayerInfo/language={language}_id={id}")
def getPlayerInfo(language: str, id: int):
    """
    Cette fonction donne les informations du joueur en fonction de la langue renseignée, le nom complet, et l'identifiant TransferMarkt renseigné. La langue doit être les 2 lettres de l'extension de domaine associée, le nom doit être le même que celui fourni par searchPlayer à savoir avec un espace de séparation et l'ID doit être sous forme numérique.
    """ 
    #return {'r' : 'r'}
    language = correctDomainExtension(language)
    domain = 'https://www.transfermarkt.' + language      
    url = domain + '/spieler/profil/spieler/' + str(id)
    #Brouillage des requêtes
    userAgent = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0'
    headers = {'Content-Type': 'text/html', 'user-agent': str(userAgent)}
    response = requests.get(url, headers=headers)
    if response.ok:
        soup = BeautifulSoup(response.text, "lxml")
        rawCellsListDataTable = soup.select('div[class*="info-table info-table--right-space"]')
        if rawCellsListDataTable == [] :
            return {"error" : "This player ID doesn't exists."}
        cellsListDataTable = rawCellsListDataTable[0].findAll('span')
        citizenshipList =[]
        specialMarketValue = False
        if language == 'fr':
            originNameTitle = "Nom dans le pays d'origine:"
            fullNameTitle = "Nom complet:"
            dateOfBirthTitle = "Naissance (âge):"
            placeOfBirthTitle = "Lieu:"
            heightTitle = "Taille:"
            citizenshipTitle = 'Nationalité:'
            positionTitle = 'Position:'
            footTitle = 'Pied:'
            agentTitle = 'Agent du joueur:'
            clubTitle = 'Club actuel:'
            inTeamSinceTitle = "Dans l'équipe depuis:"
            contractUntilTitle = 'Contrat jusqu’à:'
            lastProlDateTitle = 'Date de la dernière prolongation:'
            outfitterTitle = 'Équipementier:'
            socialMediaTitle = 'Réseaux sociaux:'
        elif language == 'co.uk' or language == 'us' or language == 'co.in' or language == 'co.kr'or language =='co.za' or language == 'com':                
            originNameTitle = "Name in home country:"
            fullNameTitle = "Full name:"
            dateOfBirthTitle = "Date of birth/Age:"
            placeOfBirthTitle = "Place of birth:"
            heightTitle = "Height:"
            citizenshipTitle = 'Citizenship:'
            positionTitle = 'Position:'
            footTitle = 'Foot:'
            agentTitle = 'Player agent:'
            clubTitle = 'Current club:'
            inTeamSinceTitle = "Joined:"
            contractUntilTitle = 'Contract expires:'
            lastProlDateTitle = 'Date of last contract extension:'
            outfitterTitle = 'Outfitter:'
            socialMediaTitle = 'Social-Media:'
        elif language == 'es' or language == 'com.ar' or language == 'co' or language == 'mx' or language == 'pe':                
            originNameTitle = "Nombre en país de origen:"
            fullNameTitle = "Nombre completo:"
            dateOfBirthTitle = "F. Nacim./Edad:"
            placeOfBirthTitle = "Lugar de nacimiento:"
            heightTitle = "Altura:"
            citizenshipTitle = 'Nacionalidad:'
            positionTitle = 'Posición:'
            footTitle = 'Pie:'
            agentTitle = 'Agente:'
            clubTitle = 'Club actual:'
            inTeamSinceTitle = "Fichado:"
            contractUntilTitle = 'Contrato hasta:'
            lastProlDateTitle = 'Última renovación:'
            outfitterTitle = 'Proveedor:'
            socialMediaTitle = 'Redes sociales:'
        elif language == 'de' or language =='at' or language =='ch':                
            originNameTitle = "Name im Heimatland:"
            fullNameTitle = "Vollständiger Name:"
            dateOfBirthTitle = "Geb./Alter:"
            placeOfBirthTitle = "Geburtsort:"
            heightTitle = "Größe:"
            citizenshipTitle = 'Nationalität:'
            positionTitle = 'Position:'
            footTitle = 'Fuß:'
            agentTitle = 'Spielerberater:'
            clubTitle = 'Aktueller Verein:'
            inTeamSinceTitle = "Im Team seit:"
            contractUntilTitle = 'Vertrag bis:'
            lastProlDateTitle = 'Letzte Verlängerung:'
            outfitterTitle = 'Ausrüster:'
            socialMediaTitle = 'Social Media:'  
        elif language == 'it':                
            originNameTitle = "Nome completo:"
            fullNameTitle = "Nome d'arte:"
            dateOfBirthTitle = "Nato il:"
            placeOfBirthTitle = "Luogo di nascita:"
            heightTitle = "Altezza:"
            citizenshipTitle = 'Nazionalità:'
            positionTitle = 'Posizione:'
            footTitle = 'Piede:'
            agentTitle = 'Procuratore:'
            clubTitle = 'Squadra attuale:'
            inTeamSinceTitle = "In rosa da:"
            contractUntilTitle = 'Scadenza:'
            lastProlDateTitle = 'Ultimo prolungamento:'
            outfitterTitle = 'Fornitore:'            
            socialMediaTitle = 'Social Media:' 
        elif language == 'ro':                
            originNameTitle = "Numele în țara de origine:"
            fullNameTitle = "Nume și prenume:"
            dateOfBirthTitle = "Data nașterii/Vârsta:"
            placeOfBirthTitle = "Locul nașterii:"
            heightTitle = "Înălţime:"
            citizenshipTitle = 'Cetățenie:'
            positionTitle = 'Poziția:'
            footTitle = 'Picior:'
            agentTitle = 'Agent de jucători:'
            clubTitle = 'Clubul actual:'
            inTeamSinceTitle = "S-a alăturat:"
            contractUntilTitle = 'Contractul expiră:'
            lastProlDateTitle = 'Data ultimei prelungiri a contractului:'
            outfitterTitle = 'Comerciant:'            
            socialMediaTitle = 'Social media:' 
        elif language == 'pt':                
            originNameTitle = "Nome completo:"
            fullNameTitle = "Nome completo:"
            dateOfBirthTitle = "Nasc./Idade:"
            placeOfBirthTitle = "Naturalidade:"
            heightTitle = "Altura:"
            citizenshipTitle = 'Nacionalidade:'
            positionTitle = 'Posição:'
            footTitle = 'Pé:'
            agentTitle = 'Empresário:'
            clubTitle = 'Clube atual:'
            inTeamSinceTitle = "Na equipa desde:"
            contractUntilTitle = 'Contrato até:'
            lastProlDateTitle = 'Última renovação:'
            outfitterTitle = 'Equipador:'            
            socialMediaTitle = 'Redes Sociais:' 
        elif language == 'com.br':
            originNameTitle = "Nome no país de origem:"
            fullNameTitle = "Nome completo:"
            dateOfBirthTitle = "Nasc./Idade:"
            placeOfBirthTitle = "Local de nascimento:"
            heightTitle = "Altura:"
            citizenshipTitle = 'Nacionalidade:'
            positionTitle = 'Posição:'
            footTitle = 'Pé:'
            agentTitle = 'Empresários:'
            clubTitle = 'Clube atual:'
            inTeamSinceTitle = "No time desde:"
            contractUntilTitle = 'Contrato até:'
            lastProlDateTitle = 'Última renovação de contrato:'
            outfitterTitle = 'Fornecedor:'            
            socialMediaTitle = 'Redes Sociais:'                 
        elif language == 'gr':                
            originNameTitle = "Όνομα στη χώρα καταγωγής:"
            fullNameTitle = "Ονοματεπώνυμο:"
            dateOfBirthTitle = "ΗΓ/Ηλικία:"
            placeOfBirthTitle = "Τόπος γέννησης:"
            heightTitle = "Ύψος:"
            citizenshipTitle = 'Εθνικότητα:'
            positionTitle = 'Θέση:'
            footTitle = 'Πόδι:'
            agentTitle = 'Ατζέντης:'
            clubTitle = 'Τρέχουσα ομάδα:'
            inTeamSinceTitle = "Από:"
            contractUntilTitle = 'Λήξει συμβολαίου:'
            lastProlDateTitle = 'Τελευταία επέκταση συμβολαίου:'
            outfitterTitle = 'Εξοπλιστής:'            
            socialMediaTitle = 'Μέσα κοινωνικής δικτύωσης:' 
        elif language == 'co.id':                
            originNameTitle = "Nama di negara asal:"
            fullNameTitle = "Nama lengkap:"
            dateOfBirthTitle = "Tanggal lahir / Umur:"
            placeOfBirthTitle = "Tempat kelahiran:"
            heightTitle = "Tinggi:"
            citizenshipTitle = 'Kewarganegaraan:'
            positionTitle = 'Posisi:'
            footTitle = 'Kaki dominan:'
            agentTitle = 'Agen pemain:'
            clubTitle = 'Klub Saat Ini:'
            inTeamSinceTitle = "Bergabung:"
            contractUntilTitle = 'Kontrak berakhir:'
            lastProlDateTitle = 'Perpanjangan kontrak terakhir:'
            outfitterTitle = 'Penjual pakaian swasta:'            
            socialMediaTitle = 'Media Sosial:' 
            specialMarketValue = True
        elif language == 'com.tr':                
            originNameTitle = "Anavatandaki isim:"
            fullNameTitle = "Tam adı:"
            dateOfBirthTitle = "Doğum tarihi/Yaş:"
            placeOfBirthTitle = "Doğum yeri:"
            heightTitle = "Boy:"
            citizenshipTitle = 'Uyruk:'
            positionTitle = 'Mevki:'
            footTitle = 'Ayak:'
            agentTitle = 'Temsilci:'
            clubTitle = 'Güncel kulüp:'
            inTeamSinceTitle = "Takıma katılma tarihi:"
            contractUntilTitle = 'Sözleşme:'
            lastProlDateTitle = 'Son sözleşme uzatma tarihi:'
            outfitterTitle = 'Donatıcı:'
            socialMediaTitle = 'Sosyal medya:' 
        elif language == 'be' or language =='nl':                
            originNameTitle = "Naam in thuisland:"
            fullNameTitle = "Volledige naam:"
            dateOfBirthTitle = "Geb./leeftijd:"
            placeOfBirthTitle = "Geboorteplaats:"
            heightTitle = "Lengte:"
            citizenshipTitle = 'Nationaliteit:'
            positionTitle = 'Positie:'
            footTitle = 'Voet:'
            agentTitle = 'Spelersmakelaar'
            clubTitle = 'Actuele club:'
            inTeamSinceTitle = "In het team sinds:"
            contractUntilTitle = 'Contract tot en met:'
            lastProlDateTitle = 'Laatste verlenging:'
            outfitterTitle = 'Bevoorrader:'
            socialMediaTitle = 'Social media:' 
        elif language == 'pl':                
            originNameTitle = "Nazwisko w kraju pochodzenia:"
            fullNameTitle = "Pełna nazwa:"
            dateOfBirthTitle = "Urodz./Wiek:"
            placeOfBirthTitle = "Miejsce urodzenia:"
            heightTitle = "Wzrost:"
            citizenshipTitle = 'Narodowość:'
            positionTitle = 'Pozycja:'
            footTitle = 'Noga:'
            agentTitle = 'Menadżerowie:'
            clubTitle = 'Obecny klub:'
            inTeamSinceTitle = "W drużynie od:"
            contractUntilTitle = 'Umowa do:'
            lastProlDateTitle = 'Ostatnie przedłużenie umowy:'
            outfitterTitle = 'Sponsor wyposażenia:'
            socialMediaTitle = 'Portale społecznościowe:' 
        elif language == 'jp':
            originNameTitle = "母国語表記:"
            fullNameTitle = "フルネーム:"
            dateOfBirthTitle = "生年月日/年齢:"
            placeOfBirthTitle = "出生地:"
            heightTitle = "身長:"
            citizenshipTitle = '国籍:'
            positionTitle = 'ポジション:'
            footTitle = '利き足:'
            agentTitle = '代理人:'
            clubTitle = '現在のクラブ:'
            inTeamSinceTitle = "加入日:"
            contractUntilTitle = '契約満了日:'
            lastProlDateTitle = '契約延長日:'
            outfitterTitle = 'スパイク企業:'
            socialMediaTitle = 'ソーシャメディア:'
        careerEnded = False
        agent = None
        outfitter = None
        socialMedia = []
        originName = None
        fullName = ''
        lastProlDate = None
        placeOfBirth = None
        age = None
        height = None
        foot = None
        dateOfBirth = None
        inTeamSince = None
        contractUntil = None
        marketValue = None
        position = None
        club = None
        for indexCell in range(len(cellsListDataTable)):
            titleOnGoing = cellsListDataTable[indexCell].text
            if titleOnGoing == originNameTitle:
                originName = cellsListDataTable[indexCell+1].text
            elif titleOnGoing == fullNameTitle :
                fullName = cellsListDataTable[indexCell+1].text
            elif titleOnGoing == placeOfBirthTitle :
                rawPlaceOfBirth = cellsListDataTable[indexCell+1].text.replace('\n','')
                placeOfBirth = rawPlaceOfBirth[0 : len(rawPlaceOfBirth)-3]
            elif titleOnGoing == dateOfBirthTitle :
                rawDateOfBirthList = cellsListDataTable[indexCell+1].text
                dateOfBirthList = rawDateOfBirthList.replace("\n", '').split(' (')
                dateOfBirth = dateOfBirthList[0]
                age = dateOfBirthList[1].replace(')','').replace('                                                ','')
            elif titleOnGoing == heightTitle :
                height = cellsListDataTable[indexCell+1].text
            elif titleOnGoing == citizenshipTitle :
                imgCitizenshipList = cellsListDataTable[indexCell+1].findAll('img')
                for element in imgCitizenshipList:
                    citizenshipList.append(element['title'])
            elif titleOnGoing == positionTitle :
                position = cellsListDataTable[indexCell+1].text.replace('\n                    ','').replace('                ','')
            elif titleOnGoing == footTitle :
                foot = cellsListDataTable[indexCell+1].text
            elif agentTitle in titleOnGoing :
                rawAgent = cellsListDataTable[indexCell+1].text.replace('\n', '')
                agent = rawAgent[0 : len(rawAgent) - 1]
            elif clubTitle in titleOnGoing :
                if "https://tmssl.akamaized.net/images/wappen/small/123.png?lm=1456997286" in str(cellsListDataTable[indexCell+1].find('img')['srcset']) :
                    careerEnded = True
                    club = None
                else:
                    careerEnded = False
                    rawClub = cellsListDataTable[indexCell+1].text.replace('\n\n\n\n', '')
                    club = rawClub[0 : len(rawClub)-1]
            elif titleOnGoing == inTeamSinceTitle :
                inTeamSince = cellsListDataTable[indexCell+1].text.replace('\n                            ', '').replace('                        ','')
            elif titleOnGoing == contractUntilTitle :
                contractUntil = cellsListDataTable[indexCell+1].text
            elif titleOnGoing == lastProlDateTitle :
                lastProlDate = cellsListDataTable[indexCell+1].text
            elif titleOnGoing == outfitterTitle :
                outfitter = cellsListDataTable[indexCell+1].text
            elif titleOnGoing == socialMediaTitle :
                socialMediaList = cellsListDataTable[indexCell+1].findAll('a')
                for cpt in socialMediaList :
                    socialMedia.append(cpt['href'])
        shirtNumber = None
        fullNameFromBigHeader = soup.find('h1', {'class' : 'data-header__headline-wrapper'}).text
        rawNameList = fullNameFromBigHeader.split(" ")
        rawShirtNumber = rawNameList[24]
        shirtNumber = rawShirtNumber[1 : len(rawShirtNumber)]
        if rawNameList[len(rawNameList)-4] == "" : #Si le nom complet est composé de 2 mots
            name = rawNameList[len(rawNameList)-2]
            firstname = rawNameList[len(rawNameList)-3]
        else : #Si le nom complet est composé de plus de 2 mots
            name = rawNameList[len(rawNameList)-3] + ' ' + rawNameList[len(rawNameList)-2] 
            if rawNameList[len(rawNameList)-5] == "" :
                firstname = rawNameList[len(rawNameList)-4]
            else : #Si le prénom est composé de 2 mots sans tiret les séparant (cas rare)
                firstname = rawNameList[len(rawNameList)-5] + " " + rawNameList[len(rawNameList)-4]
        #Parfois récupère un prenom-nom au lieu de Prénom Nom
        if " " not in fullName :
            fullName = firstname + ' ' + name
        firstname = firstname.replace('\n', '') 
        name = name.replace('\n', '')
        #Recherche de la valeur marchande se trouvant dans une balise indétectable par FastAPI
        description = soup.find('meta', {'name' : 'description'})['content']
        rawBoxMarketValue = soup.find('div', {'class' : 'data-header__box--small'})
        if rawBoxMarketValue != None :
            boxMarketValue = rawBoxMarketValue.text.split(' ')
            if(specialMarketValue == False) :
                marketValue = boxMarketValue[0].replace('\n', '') + ' ' + boxMarketValue[1] + ' ' + boxMarketValue[2] 
            else :
                marketValue = boxMarketValue[0].replace('\n', '')
        #Calcul de l'historique des transferts
        #transfertsHistoric = []
        #tabless = soup.find('tm-transfer-history')
        #return str(tabless)
        #Calcul des stats   
        stats = [] 
        urlStat = domain + '/spieler/leistungsdatendetails/spieler/' + str(id)
        headers = {'Content-Type': 'text/html', 'user-agent': str(userAgent)}
        response = requests.get(urlStat, headers=headers)
        if response.ok:
            soup = BeautifulSoup(response.text, "lxml")
            table = soup.find('div', {'id' : 'yw1'})
            oddLines = table.findAll('tr', {'class' : 'odd'})
            evenLines = table.findAll('tr', {'class' : 'even'})
            #Calcul de nombre de ligne à analyser sachant que les index sont alternés
            nbLines = len(oddLines) + len(evenLines)
            rangeLines = math.trunc(nbLines/2)
            oddNumber = False
            if nbLines % 2 == 1:
                rangeLines += 1
                oddNumber = True
            for index in range(rangeLines):
                #Alternance entre la ligne de class Odd et celle de classe Even
                for oddOrEven in range(2):
                    if oddOrEven == 0 :
                        lines = oddLines
                    else:
                        if (oddNumber == True) and (index == rangeLines - 1):
                            break 
                        else: 
                            lines = evenLines
                    #Liste des TD dont les valeurs de texte correspondent ensuite à chaque case
                    tdList = lines[index].findAll('td')
                    #return str(tdList[0])
                    stats.append({
                        'season' : tdList[0].text,
                        'competition' : tdList[2].text,
                        'club' : str(tdList[3].find('img')['title']),
                        'matchs' : tdList[4].text,
                        'buts' : tdList[5].text,
                        'decisivePass' : tdList[6].text,
                        'yellowOrangeRedCards' : tdList[7].text,
                        'minutesPlayed' : tdList[8].text,
                    })     
        #Historique des blessures
        injuriesHistoric = [] 
        urlInj = domain + '/spieler/verletzungen/spieler/' + str(id)
        response = requests.get(urlInj, headers=headers)
        if response.ok:
            soup = BeautifulSoup(response.text, "lxml")
            table = soup.find('div', {'id' : 'yw1'})
            oddLines = table.findAll('tr', {'class' : 'odd'})
            evenLines = table.findAll('tr', {'class' : 'even'})
            #Calcul de nombre de ligne à analyser sachant que les index sont alternés
            nbLines = len(oddLines) + len(evenLines)
            rangeLines = math.trunc(nbLines/2)
            oddNumber = False
            if nbLines % 2 == 1:
                rangeLines += 1
                oddNumber = True
            for index in range(rangeLines):
                #Alternance entre la ligne de class Odd et celle de classe Even
                for oddOrEven in range(2):
                    if oddOrEven == 0 :
                        lines = oddLines
                    else:
                        if (oddNumber == True) and (index == rangeLines - 1):
                            break 
                        else: 
                            lines = evenLines
                    #Liste des TD dont les valeurs de texte correspondent ensuite à chaque case
                    tdList = lines[index].findAll('td')
                    missedClubs = []
                    clubMissedList = tdList[5].findAll('img')
                    for clubOnGoing in clubMissedList :
                        missedClubs.append(clubOnGoing['alt'])
                    injuriesHistoric.append({
                        'season' : tdList[0].text,
                        'injury' : tdList[1].text,
                        'from' : tdList[2].text,
                        'until' : tdList[3].text,
                        'daysDuration' : tdList[4].text,
                        'club' : missedClubs,
                        'missedMatch' : tdList[5].text
                    })     
        return {
                'transferMarktId' : id,
                'url' : url,
                'name' : name,
                'description' : description,
                'fullName' : fullName.replace('\n',''),
                'imageURL' : soup.find('img', {'class' : 'data-header__profile-image'})['src'],
                'dateOfBirth' : dateOfBirth,
                'placeOfBirth' : placeOfBirth,
                'age' : age,
                'height' : height,
                'citizenship' : citizenshipList,
                'isRetired' : careerEnded,
                'position' : position,
                'foot' : foot,
                'shirtNumber' : shirtNumber,
                'club' : club,
                'marketValue' : marketValue,
                'agent' : agent,
                'outfitter' : outfitter,
                'socialMedia' : socialMedia,
                'stats' : stats,
                'updatedAt' : None,
                'originName' : originName,
                'inTeamSince' : inTeamSince,
                'contractUntil' : contractUntil,
                'lastProlDate' : lastProlDate,
                'injuriesHistoric' : injuriesHistoric 
                }
                
    

@app.get("/getDashboardClub/language={language}_id={id}")
def searchClub(language: str, id: int):
    """
   Cette fonction donne le dashboard contenant tous les joueurs en fonction de l'identifiant du club en question et en fonction de la langue. La langue doit être les 2 lettres de l'extension de domaine associée.
    """ 
    language = correctDomainExtension(language)
    domain = 'https://www.transfermarkt.' + language      
    url = domain + '/spieler/startseite/verein/' + str(id)
    #Brouillage des requêtes
    userAgent = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0'
    headers = {'Content-Type': 'text/html', 'user-agent': str(userAgent)}
    response = requests.get(url, headers=headers)
    playersList = []    
    if response.ok:
        soup = BeautifulSoup(response.text, "lxml")
        #Nombre de tableaux principaux
        principalBox = soup.find('div', {'class' : 'box'})
        
        oddLines = principalBox.findAll('tr', {'class' : 'odd'})
        evenLines = principalBox.findAll('tr', {'class' : 'even'})
        #Calcul de nombre de ligne à analyser sachant que les index sont alternés
        nbLines = len(oddLines) + len(evenLines)
        rangeLines = math.trunc(nbLines/2)
        oddNumber = False
        if nbLines % 2 == 1:
            rangeLines += 1
            oddNumber = True
        for index in range(rangeLines):
            print(str(index) + ' ' + str(rangeLines))
            #Alternance entre la ligne de class Odd et celle de classe Even
            for oddOrEven in range(2):
                if oddOrEven == 0 :
                    lines = oddLines
                else:
                    if (oddNumber == True) and (index == rangeLines - 1):
                        break 
                    else: 
                        lines = evenLines
                #Liste des TD dont les valeurs de texte correspondent ensuite à chaque case
                tdList = lines[index].findAll('td')
                #Création du json joueur
                print('FEEE')
                firstCaseList = tdList[1].text.split('\n\n\n\n\n')
                #Calcul date de naissance et age
                rawDateOfBirthList = tdList[5].text
                dateOfBirthList = rawDateOfBirthList.split(' (')
                dateOfBirth = dateOfBirthList[0]
                age = dateOfBirthList[1]
                #Calcul des nationalités
                citizenshipList = []
                imgCitizenshipList = tdList[6].findAll('img')
                for element in imgCitizenshipList:
                    citizenshipList.append(element['title'])
                playersList.append({
                    'shirtNumber' : tdList[0].text,
                    'playerName' : firstCaseList[0].replace('\n\n\n\n \n\n\n                ','').replace('            ',''),
                    'position' : firstCaseList[1].replace('        \n\n\n','').replace('            ',''),
                    'playerUrl' : domain + tdList[1].find('a')['href'],
                    'playerImageUrl' : str(tdList[1].find('tr').find('img')['data-src']),
                    'dateOfBirth' : dateOfBirth,
                    'age' : age.replace(')',''),
                    'citizenship' : citizenshipList,
                    'marketValue' : tdList[7].text
                })            
        return { 'players' : playersList }
                
    
