import basespider
from models import Article,User
from utils.constant import *
import re
import json


class Unsplash(basespider.BaseSpider):
    def __init__(self):

        self.collist = None
        self.colIndex = 1
        self.picList = []

    def prepareOneCollection(self):
        colUrl = "https://unsplash.com/collections/curated/"+str(self.colIndex)
        self.colIndex = self.colIndex+1
        picList = self.getPhotosJSON(colUrl)
        return picList


    def getPhotosJSON(self,url):
        colHtml = self.getHtml(url)
        if colHtml == None:
            return None
        j=0
        start=9999
        end=9999
        sb = ""
        for line in colHtml.split('\n'):
            if '__ASYNC_PROPS__' in line:
                start=j
            if j>start and j<end and '</script>' in line:
                end=j
            if j>start and j<end:
                sb=sb+line
            j=j+1
        #sb = sb[0:-2]
        obj0 = json.loads(sb,encoding="utf-8")
        picList = obj0['asyncPropsPhotoFeed']['photos']
        print len(picList)
        return picList

    def getSource(self):
        return ORI_UNSPLASH

    def getNext(self):
        if len(self.picList)==0:
            tempPicList = self.prepareOneCollection()
            if tempPicList!= None:
                self.picList.extend(tempPicList)
            else:
                return None
        return self.picList.pop(0)

    def processSingle(self, obj):
        try:
            picUrl = obj['urls']['raw']
            originUrl = obj['links']['html']
            origName = obj['id']
            fileName = origName+'.jpg'

            count = self.getDB().session.query(Article).filter(Article.origin_url == originUrl).count()
            if count > 0:
                return None

            user = obj['user']
            author_url =user['links']['html']
            author = self.getDB().session.query(User).filter(User.origin_url == author_url).first()
            if author is None:
                author = User()
                author.description = user['bio']
                author.nickname = user['name']
                author.username = user['username']
                author.is_imported = True
                author.origin = self.getSource()
                author.origin_url = author_url
                author.status = STATUS_NORMAL
                author.role = ROLE_AUTHOR

                self.saveAuthor(author)

            self.article = Article()
            self.article.origin = self.getSource()
            self.article.origin_url = originUrl
            self.article.author_id = author.id
            self.article.pic_url = picUrl
            self.article.file_name = fileName
            self.article.title = origName
            result = self.saveImage(picUrl, fileName)
            if result is True:
                return self.article
            else:
                return result
        except Exception,e:
            self.logger.error(e)
            return False
        return False


