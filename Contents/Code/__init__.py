# -*- coding: utf-8 -*-
from PMS import *
from Crypto.Cipher import DES
import time
import datetime
import base64

####################################################################################################
# Author 		: GuinuX
# Contributors 	: Pierre
####################################################################################################
# CHANGELOG : - Pierre : Some changes to be Compatible With PLEX 8
####################################################################################################

PLUGIN_PREFIX = '/video/m6replay'
NAME          = 'M6Replay'
ART           = 'art-default.jpg'
ICON          = 'icon-default.png'

CATALOG_XML = ""
IMAGES_SERVER = ""
CONFIGURATION_URL = "http://www.m6replay.fr/files/configurationm6_lv3.xml"

####################################################################################################

def Start():

	Plugin.AddPrefixHandler(PLUGIN_PREFIX, VideoMainMenu, NAME, ICON, ART)
	Plugin.AddViewGroup("Coverflow", viewMode="Coverflow", mediaType="items")
	Plugin.AddViewGroup("InfoList", viewMode="InfoList", mediaType="items")
	
	MediaContainer.art = R(ART)
	MediaContainer.title1 = NAME
	DirectoryItem.thumb = R(ICON)
	HTTP.SetcacheTime = CACHE_1HOUR


def VideoMainMenu():

	global CATALOG_XML
	global IMAGES_SERVER
	
	dir = MediaContainer(viewGroup="Coverflow")
	xml = HTTP.Request(CONFIGURATION_URL)

	IMAGES_SERVER = XML.ElementFromString( xml ).xpath("/config/path/image")[0].text
	EnCryptCatalogueURL = XML.ElementFromString( xml ).xpath("/config/services/service[@name='GetEnCryptCatalogueService']/url")[0].text
	
	cryptedXML = HTTP.Request(EnCryptCatalogueURL,cacheTime=CACHE_1HOUR)	
	decryptor = DES.new( "ElFsg.Ot", DES.MODE_ECB )
	CATALOG_XML = decryptor.decrypt( base64.decodestring( cryptedXML ) )
	
	#
	# TODO : Tester si le decryptage s'est bien passé.
	#
	
	finXML = CATALOG_XML.find( "</template_exchange_WEB>" ) + len( "</template_exchange_WEB>" )
	CATALOG_XML = CATALOG_XML[ : finXML ]
	
	for category in XML.ElementFromString(CATALOG_XML).xpath("//template_exchange_WEB/categorie"):
		nom = category.xpath("./nom")[0].text
		image = IMAGES_SERVER + category.get('big_img_url')
		idCategorie = category.get('id')
		dir.Append(Function(DirectoryItem(ListShows, title = nom, thumb = image), idCategorie = idCategorie, nomCategorie = nom))
	
	return dir


def ListShows(sender, idCategorie, nomCategorie):

	global CATALOG_XML
	global IMAGES_SERVER
	
	dir = MediaContainer(viewGroup="Coverflow", title1 = "M6 Replay", title2 = nomCategorie)
	search = "/template_exchange_WEB/categorie[@id='" + idCategorie + "']/categorie"

	for item in XML.ElementFromString(CATALOG_XML).xpath(search):
		nom = item.xpath("nom")[0].text
		image = IMAGES_SERVER + item.get('big_img_url')
		idCategorie = item.get('id')

		dir.Append(Function(DirectoryItem(ListEpisodes, title = nom, thumb = image), idCategorie = idCategorie, nomCategorie = nom))
	
	return dir


def ListEpisodes(sender, idCategorie, nomCategorie):

	global CATALOG_XML
	global IMAGES_SERVER
		
	dir = MediaContainer(viewGroup="InfoList", title1 = "M6 Replay", title2 = nomCategorie)
	search = "//template_exchange_WEB/categorie/categorie[@id=" + idCategorie + "]/produit"
	
	for episode in XML.ElementFromString(CATALOG_XML).xpath(search):
		Log(XML.StringFromElement(episode))
		idProduit = episode.get('id')
		nom = episode.xpath("./nom")[0].text
		description = episode.xpath("./resume")[0].text
		image = IMAGES_SERVER + episode.get('big_img_url')
		url = episode.xpath("./fichemedia")[0].get('video_url')[:-4]
		lienValideVideo = "rtmp://m6dev.fcod.llnwd.net:443/a3100/d1/"
		date_diffusion = datetime.datetime(*(time.strptime(episode.xpath("./diffusion")[0].get('date'), "%Y-%m-%d %H:%M:%S")[0:6])).strftime("%d/%m/%Y à %Hh%M")
		str_duree = episode.xpath("./fichemedia")[0].get('duree')
		duree = long(str_duree) / 60
		dureevideo = long(str_duree)*1000
		description = description + '\n\nDiffusé le ' + date_diffusion + '\n' + 'Durée : ' + str(duree) + ' mn'
		dir.Append(RTMPVideoItem(url = lienValideVideo, clip = url, title = nom, subtitle = nomCategorie, summary = description, duration = dureevideo, thumb = image))
	return dir
	
	
