import requests
import json
from bs4 import BeautifulSoup
import re
import io

def searchDepartments():
	res = requests.get("https://video.ethz.ch/lectures.html", headers={'User-Agent': 'Mozilla/5.0'})
	soup = BeautifulSoup(res.content, features="lxml")
	departments = soup.find("li", {"class": "cur"}).find("ul").find_all("li")
	departmentList = []

	for department in departments:
		content = department.find("a").contents
		departmentList.append(re.findall("D-[A-Z][A-Z][A-Z][A-Z]", str(content))[0])

	return departmentList

def searchLectures(department):
	res = requests.get("https://video.ethz.ch/lectures/" + department.lower() + ".html", headers={'User-Agent': 'Mozilla/5.0'})
	soup = BeautifulSoup(res.content, features="lxml")
	lectures = soup.find("ul", {"class": "level0"}).find("li").find("ul").find("li", {"class": "cur"}).find("ul").find("li").find("ul").find("li").find("ul").find_all("li")
	lectureList = []

	for lecture in lectures:
		content = lecture.find("a")

		name = re.search("\\r\\n            (.+)", str(content.contents[0])).group(1)
		lectureList.append({"Link": content["href"], "Name": name})

	return lectureList

def getVideoList(lecture):
	lecture = "https://video.ethz.ch" + lecture
	res = requests.get(lecture, headers={'User-Agent': 'Mozilla/5.0'})
	soup = BeautifulSoup(res.content, features="lxml")
	videos = soup.find("div", {"id": "filter-container"}).find_all("div", {"class": "newsListBox"})
	return videos

def extractInfos(video):
	soup = BeautifulSoup(str(video), features="lxml")
	link = soup.find("a")["href"]
	title = soup.find("h2").contents[0]
	date = re.search("\d\d\.\d\d\.\d\d\d\d", str(soup.find("p")))[0]
	return link, title, date