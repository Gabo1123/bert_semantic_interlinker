#HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH
keyword= 'tecnis eyhance'  
# change the keyword to whatever you want, for example keyword = 'buy backlink'
#HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH
# Parámetros opcionales
idioma = 'en' # español => por ejemplo para inglés usar idioma = 'en'
pais = 'en-us' # España => por ejemplo para Inglaterra usar pais = 'uk'
nivelesScrapeo = 2 # Si quieres más resultados usa 2. A partir de 3 necesitarás proxies...
loopPreguntasEnlugarDeBusquedas = True # True hace loop pusando preguntas PAA en lugar de hacer el loop con búsquedas relacionadas
#HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH

#!pip install pyopenSSl --upgrade
!pip install selenium-wire
from seleniumwire import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
#!apt update
#!apt install chromium-chromedriver

options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument("user-agent=Mozilla/5.0")
options.add_argument("--window-size=1366,768")#360,851

# iniciamos selenium
wd = webdriver.Chrome(options=options)


urlInicial = f"https://www.google.com/search?hl={idioma}&gl={pais}&q={keyword}&oq={keyword}"

scrapeado = []
contadorPreguntas = []
contadorBusquedas = []
contadorSuggest = []

googleNosHaCazado = False

# instalamos dependencias
!pip install treelib

from treelib import Node, Tree
from bs4 import BeautifulSoup
import requests
import random



# Función general => ojo se llama a si misma.
def busquedaGlobal(busquedasX, nivel):
  if googleNosHaCazado: return
  print("--------------------------")
  print(f"         Nivel {nivel}")
  print("--------------------------")

  subBusquedasRelacionadas = []
  
  for busqueda in busquedasX:
    subBusquedas = busquedaIndividual(busqueda, nivel+1)
    subBusquedasRelacionadas.extend(subBusquedas)
  
  if nivel < nivelesScrapeo:
    busquedaGlobal(subBusquedasRelacionadas, nivel +1) # con cuidado con bucle infinito

# función de scrapeo de cada búsqueda/pregunta
def busquedaIndividual(busqueda0X, nivel):
  busqueda0 = busqueda0X[0]
  url0 = busqueda0X[1] # opción url0 = f"https://www.google.com/search?hl={idioma}&gl={pais}&q={busqueda0}&oq={busqueda0}"
  
  global  googleNosHaCazado
  if busqueda0.lower() in scrapeado or googleNosHaCazado == True: return []
  
  preguntas = []
  busquedas = []
  
  tree = Tree() # arbol para reprensentarlo
  tree.create_node(busqueda0, busqueda0.lower())  # root node        
    
  wd.get(url0) # navegamos hasta la url
  
  if ("URL: https://www.google.com/search?" in wd.page_source): # ¿Nos ha cazado google?
    googleNosHaCazado = True

    if nivel == 1:
      print("-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------")
      print("Sorry Google ha cazado la IP, para seguir scrapeando elimina el entorno de ejecución (En el menú, Entorno de ejecución/desconectarse y eliminar...) o haz una copia de este colab (archivo/guardar una copia en drive) y dale al play")
      print("-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------")
    else:
      print("Google ens Roba, digo... Sorry Google nos ha cazado, fin del scrapeo de esta keyword")
    
    return []

  if nivel == 1:
    acepto = wd.find_elements(by=By.CSS_SELECTOR, value="input[value='Acepto']")
    if len(acepto) > 0:
      acepto[0].click() 

  comienza = random.randint(100, 500)/1000 # pongamos una pequeña espera random
  time.sleep(comienza)
  
  # recupero preguntas frecuentes
  PAA = wd.find_elements(by=By.CSS_SELECTOR, value="[class='xpc']") 
  if len(PAA) > 0 : tree.create_node("Preguntas Frecuentes", "Preguntas Frecuentes" , parent= busqueda0.lower())
  for boton in PAA:
    enlaces = boton.find_elements(by=By.TAG_NAME, value="a")
    for enlace in enlaces:
      href = enlace.get_attribute('href')
      if "/search" in href:
        contadorPreguntas.append(boton.text.strip().lower())
        if boton.text.strip() in tree: continue
        try:
          tree.create_node(boton.text.strip(), boton.text.strip().lower(), parent= "Preguntas Frecuentes")
        except:
          continue # en algunos casos excepcionales el texto a añadir al arbol es demasiado largo meda pereza investigarlos
        preguntas.append([boton.text.strip(), href])

  # recuperamos búsquedas relacionadas
  busquedasRelacionadas = wd.find_elements(by=By.CSS_SELECTOR, value=".Q71vJc") 
  if len(busquedasRelacionadas) > 0: tree.create_node("Búsquedas Relacionadas", "Búsquedas Relacionadas" , parent= busqueda0.lower())

  for busqueda in busquedasRelacionadas:
    contadorBusquedas.append(busqueda.text.strip().lower())
    if busqueda.text.strip() in tree: continue
    try:
      tree.create_node(busqueda.text.strip().lower(), busqueda.text.strip().lower(), parent="Búsquedas Relacionadas")
    except:
      continue
    busquedas.append([busqueda.text.strip(), busqueda.get_attribute('href')] )

  # recuperamos google suggest
  sugeridos = suggest(busqueda0)
  sugeridos = [x for x in sugeridos if x !=busqueda0 and x.lower() not in tree]
  if len(sugeridos) > 0 : tree.create_node("Google Suggest", "Google Suggest" , parent= busqueda0.lower())

  for sugerido in sugeridos:
    contadorSuggest.append(sugerido.lower())
    try:
      tree.create_node(sugerido, sugerido.lower(), parent="Google Suggest")
    except:
      continue
    
  if len(tree) > 1: tree.show(key=False)

  scrapeado.append(busqueda0.lower()) # control para no repetir búsquedas

  if loopPreguntasEnlugarDeBusquedas: return preguntas # opción devolver preguntas
  return busquedas # La opción por defecto es devolver búsquedas para el loop
 
# función para recuperar datos de google suggest
def suggest(key):
  r = requests.get(f'http://suggestqueries.google.com/complete/search?output=toolbar&hl={idioma}&gl={pais}&q={key}')
  soup = BeautifulSoup(r.content, 'html.parser')
  sugg = [sugg['data'] for sugg in soup.find_all('suggestion')]
  return sugg
    
      
# Aquí empieza todo
busquedaGlobal([[keyword, urlInicial]], 0)

# Mostramos tablas de resultados
from collections import Counter # contador para mostrar en tabla
contadorPreguntas1 = [list(x) for x in Counter(contadorPreguntas).most_common()]
contadorBusquedas1 = [list(x) for x in Counter(contadorBusquedas +contadorSuggest ).most_common()]


import pandas as pd
from google.colab import data_table
# Uso una función para visualizar tablas
def pasarATabla(lista,columnas):
  lista = pd.DataFrame (lista, columns = columnas )
  lista = data_table.DataTable(lista, include_index=True, num_rows_per_page=20)
  display(lista)

if len(contadorBusquedas1) > 0:
  print("---------------------------------")
  print("Siento una conmoción en la fuerza")
  print("----------------------------------------------------------------")
  print(f"Si quieres obtener más resultados prueba con nivelesScrapeo = {nivelesScrapeo+1}")
  print("----------------------------------------------------------------")
  pasarATabla(contadorBusquedas1, ["Búsqueda relacionada", "Relevancia"])

if len(contadorPreguntas1) > 0:
  pasarATabla(contadorPreguntas1, ["Preguntas relacionadas", "Relevancia"])
