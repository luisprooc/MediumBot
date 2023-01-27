#!/usr/bin/python
# -*- coding: utf-8 -*-
# Author: Matt Flood

import os
import random
import time
from random import shuffle

import undetected_chromedriver as uc
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

# Configure constants here
EMAIL = os.getenv('MEDIUM_EMAIL', '')
PASSWORD = os.getenv('MEDIUM_PASSWORD', '')
LOGIN_SERVICE = 'Google'
DRIVER = 'Firefox'
LIKE_POSTS = False
RANDOMIZE_LIKING_POSTS = True
MAX_LIKES_ON_POST = 50
COMMENT_ON_POSTS = True
RANDOMIZE_COMMENTING_ON_POSTS = True
COMMENTS = ['Great read!', 'Good work keep it up!', 'Really enjoyed the content!', 'Very interesting!', 'Nicee!']
ARTICLE_BLACK_LIST = ['Sex', 'Drugs', 'Child Labor']
FOLLOW_USERS = False
RANDOMIZE_FOLLOWING_USERS = True
UNFOLLOW_USERS = False
RANDOMIZE_UNFOLLOWING_USERS = False
UNFOLLOW_USERS_BLACK_LIST = ['DontUnFollowMe']
USE_RELATED_TAGS = True
ARTICLES_PER_TAG = 250
VERBOSE = True

def Launch():
    """
    Launch the Medium bot and ask the user what browser they want to use.
    """
    StartBrowser()


def StartBrowser():
    """
    Based on the option selected by the user start the selenium browser.
    browserChoice: browser option selected by the user.
    """
    browser = uc.Chrome()
    #driver = uc.Chrome(use_subprocess=True)
    #wait = uc.C

    if SignInToService(browser):
        print ('Success!\n')
        MediumBot(browser)

    else:
        soup = BeautifulSoup(browser.page_source, "lxml")
        if soup.find('div', {'class':'alert error'}):
            print('Error! Please verify your username and password.')
        elif browser.title == '403: Forbidden':
            print('Medium is momentarily unavailable. Please wait a moment, then try again.')
        else:
            print('Please make sure your config is set up correctly.')

    browser.quit()


def SignInToService(browser):
    """
    Using the selenium browser passed and the config file login to Medium to
    begin the botting.
    browser: the selenium browser used to login to Medium.
    """
    signInCompleted = False
        
    print('Signing in...')

    # Sign in
    browser.get('https://medium.com/m/signin?redirect=https%3A%2F%2Fmedium.com%2F')

    signInCompleted = SignInToMedium(browser)

    return signInCompleted


def SignInToMedium(browser):
    """
    Sign into Medium using a Google account.
    browser: selenium driver used to interact with the page.
    return: true if successfully logged in : false if login failed.
    """

    signInCompleted = False
    
    time.sleep(5)
    browser.find_element(By.XPATH, "//body/div/div[@role='dialog']/div[@class='ab ac ad ae af ag']/div[@class='pw-susi-modal ah ai aj ak al am an ao ap aq ar']/div[@class='ah as at au l av aw ax ay az ba']/div[@class='bb bc l m bd n be bf bg bh az']/div[@class='bu ak']/a[1]").click()
    time.sleep(3)
    browser.find_element(By.NAME, 'identifier').send_keys(EMAIL)
    browser.find_element(By.XPATH, "//button[@class='VfPpkd-LgbsSe VfPpkd-LgbsSe-OWXEXe-k8QpJ VfPpkd-LgbsSe-OWXEXe-dgl2Hf nCP5yc AjY5Oe DuMIQc LQeN7 qIypjc TrZEUc lw1w4b']").click()
    time.sleep(3)
    browser.find_element(By.NAME, 'password').send_keys(PASSWORD)
    time.sleep(3)
    browser.find_element(By.XPATH, "//button[@class='VfPpkd-LgbsSe VfPpkd-LgbsSe-OWXEXe-k8QpJ VfPpkd-LgbsSe-OWXEXe-dgl2Hf nCP5yc AjY5Oe DuMIQc LQeN7 qIypjc TrZEUc lw1w4b']").click()
    time.sleep(20)
    #browser.get("https://medium.com/me/following/tags")
    signInCompleted = True
    

    return signInCompleted


def MediumBot(browser):
    """
    Start botting Medium
    browser: selenium browser used to interact with the page
    """

    tagURLsQueued = []
    tagURLsVisitedThisLoop = []
    articleURLsVisited = []

    # Infinite loop
    while True:

        tagURLsQueued = ScrapeUsersFavoriteTagsUrls(browser)

        while tagURLsQueued:

            articleURLsQueued = []
            shuffle(tagURLsQueued)
            tagURL = tagURLsQueued.pop()
            tagURLsVisitedThisLoop.extend(tagURL)

            # Note: This is dones this way to add some timing between liking and
            # commenting on posts to throw any bot finder logic off
            tagURLsQueued.extend(NavigateToURLAndScrapeRelatedTags(browser, tagURL, tagURLsVisitedThisLoop))
            articleURLsQueued = ScrapeArticlesOffTagPage(browser, articleURLsVisited)

            while articleURLsQueued:

                # We don't want to max out the list so check to make sure we don't overload it in mem
                if len(articleURLsVisited) > 530000000:
                    articleURLsVisited = []

                print("Tags in Queue: "+str(len(tagURLsQueued))+" Articles in Queue: "+str(len(articleURLsQueued)))
                articleURL = articleURLsQueued.pop()
                articleURLsVisited.extend(articleURL)
                LikeCommentAndFollowOnPost(browser, articleURL)

                if UNFOLLOW_USERS:
                    if not RANDOMIZE_UNFOLLOWING_USERS:
                        UnFollowUser(browser)
                    elif random.choice([True, False]):
                        UnFollowUser(browser)

        print('\nPause for 1 hour to wait for new articles to be posted\n')
        tagURLsVisitedThisLoop = [] # Reset the tags visited
        time.sleep(3600+(random.randrange(0, 10))*60)


def ScrapeUsersFavoriteTagsUrls(browser):
    """
    Scrape the urls for the user's favorite tags. We will use these to go off
    when interacting with articles.
    browser: selenium webdriver used for beautifulsoup.
    """

    browser.get("https://medium.com/me/following/tags")
    time.sleep(5)
    soup = BeautifulSoup(browser.page_source, "lxml")
    tagURLS = []
    print('Gathering your favorited tags')

    try:
        for div in soup.find_all('div', class_='u-tableCell u-verticalAlignMiddle'):
            for a in div.find_all('a'):
                if a["href"] not in tagURLS:
                    tagURLS.append(a["href"])
                    if VERBOSE:
                        print(a["href"])

    except:
        print('Exception thrown in ScrapeUsersFavoriteTagsUrls()')
        pass

    if not tagURLS or USE_RELATED_TAGS:

        if not tagURLS:
            print('No favorited tags found. Grabbing the suggested tags as a starting point.')

        try:
            for div in soup.find_all('div', class_='u-sizeFull u-paddingTop10 u-paddingBottom10 u-borderBox'):
                for a in div.find_all('a'):
                    if a["href"] not in tagURLS:
                        tagURLS.append(a["href"])
                        if VERBOSE:
                            print(a["href"])
        except:
            print('Exception thrown in ScrapeArticlesOffTagPage()')
            pass
    print('')

    return tagURLS


def NavigateToURLAndScrapeRelatedTags(browser, tagURL, tagURLsVisitedThisLoop):
    """
    Navigate to the tag url passed. If the USE_RELATED_TAGS is set scrape the
    related tags found as well.
    browser: selenium webdriver used for beautifulsoup.
    tagURL: the tag page to navigate to before scraping urls
    tagURLsVisitedThisLoop: tags we have aready visited.
        Don't want to waste time viewing them twice in a loop.
    return: list of other tag urls to add to navigate to and bot.
    """

    browser.get(tagURL)
    tagURLS = []

    if USE_RELATED_TAGS and tagURL:

        print('Gathering tags related to : '+tagURL)
        soup = BeautifulSoup(browser.page_source, "lxml")

        try:
            for ul in soup.find_all('ul', class_='tags--postTags'):
                for li in ul.find_all('li'):

                    a = li.find('a')

                    if 'followed' not in a['href'] and a['href'] not in tagURLsVisitedThisLoop:
                        tagURLS.append(a['href'])

                        if VERBOSE:
                            print(a['href'])
        except:
            print('Exception thrown in NavigateToURLAndScrapeRelatedTags()')
            pass
        print('')

    return tagURLS


def ScrapeArticlesOffTagPage(browser, articleURLsVisited):
    """
    Scrape articles to navigate to from the tag's url.
    browser: selenium webdriver used for beautifulsoup.
    articleURLsVisited: articles that have been previously visited.
    return: a list of article urls
    """

    articleURLS = []
    print('Gathering your articles for the tag :'+browser.current_url)

    browser.find_element_by_xpath('//a[contains(text(),"Latest stories")]').click()
    time.sleep(2)

    for counter in range(1,ARTICLES_PER_TAG/10):
        ScrollToBottomAndWaitForLoad(browser)

    try:
        for a in browser.find_elements_by_xpath(('//div[@class="postArticle postArticle--short '
        'js-postArticle js-trackedPost"]/div[2]/a')):
            if a.get_attribute("href") not in articleURLsVisited:
                if VERBOSE:
                    print(a.get_attribute("href"))
                articleURLS.append(a.get_attribute("href"))
    except:
        print('Exception thrown in ScrapeArticlesOffTagPage()')
        pass
    print('')

    return articleURLS


def LikeCommentAndFollowOnPost(browser, articleURL):
    """
    Like, comment, and/or follow the author of the post that has been navigated to.
    browser: selenium browser used to find the like button and click it.
    articleURL: the url of the article to navigate to and like and/or comment
    """

    browser.get(articleURL)

    if browser.title not in ARTICLE_BLACK_LIST:

        if FOLLOW_USERS:
            if not RANDOMIZE_FOLLOWING_USERS:
                FollowUser(browser)
            elif random.choice([True, False]):
                FollowUser(browser)

        ScrollToBottomAndWaitForLoad(browser)

        if LIKE_POSTS:
            if not RANDOMIZE_LIKING_POSTS:
                LikeArticle(browser)
            elif random.choice([True, False]):
                LikeArticle(browser)

        if COMMENT_ON_POSTS:
            if not RANDOMIZE_COMMENTING_ON_POSTS:
                CommentOnArticle(browser)
            elif random.choice([True, False]):
                CommentOnArticle(browser)

        print('')


def LikeArticle(browser):
    """
    Like the article that has already been navigated to.
    browser: selenium driver used to interact with the page.
    """

    likeButtonXPath = '//div[@data-source="post_actions_footer"]/button'
    numLikes = 0

    try:
        numLikesElement = browser.find_element_by_xpath(likeButtonXPath+"/following-sibling::button")
        numLikes = int(numLikesElement.text)
    except:
        pass

    try:
        likeButton = browser.find_element_by_xpath(likeButtonXPath)
        buttonStatus = likeButton.get_attribute("data-action")

        if likeButton.is_displayed() and buttonStatus == "upvote":
            if numLikes < MAX_LIKES_ON_POST:
                if VERBOSE:
                    print('Liking the article : \"'+browser.title+'\"')
                likeButton.click()
            elif VERBOSE:
                print('Article \"'+browser.title+'\" has more likes than your threshold.')
        elif VERBOSE:
            print('Article \"'+browser.title+'\" is already liked.')

    except:
        if VERBOSE:
            print('Exception thrown when trying to like the article: '+browser.current_url)
        pass


def CommentOnArticle(browser):
    """
    Comment on the article that has already been navigated to.
    browser: selenium driver used to interact with the page.
    """

    # Determine if the account has already commented on the post.
    usersName = browser.find_element_by_xpath('//div[@class="avatar"]/img').get_attribute("alt")
    alreadyCommented = False

    try:
        alreadyCommented = browser.find_element_by_xpath('//a[text()[contains(.,"'+usersName+'")]]').is_displayed()
    except:
        pass

    #TODO Find method to comment when the article is not hosted on medium.com currently
    #     found issues with the logic below when not on medium.com.
    if 'medium.com' in browser.current_url:
        if not alreadyCommented:

            comment = random.choice(COMMENTS)

            try:
                if VERBOSE:
                    print('Commenting \"'+comment+'\" on the article : \"'+browser.title+'\"')
                commentButton = browser.find_element_by_xpath('//button[@data-action="respond"]')
                commentButton.click()
                time.sleep(5)
                browser.find_element_by_xpath('//div[@role="textbox"]').send_keys(comment)
                time.sleep(20)
                browser.find_element_by_xpath('//button[@data-action="publish"]').click()
                time.sleep(5)
            except:
                if VERBOSE:
                    print('Exception thrown when trying to comment on the article: '+browser.current_url)
                pass
        elif VERBOSE:
            print('We have already commented on this article: '+browser.title)
    elif VERBOSE:
        print('Cannot comment on an article that is not hosted on Medium.com')


def FollowUser(browser):
    """
    Follow the user whose article you have already currently navigated to.
    browser: selenium webdriver used to interact with the browser.
    """

    try:
        print('Following the user: '+browser.find_element_by_xpath('//a[@rel="author cc:attributionUrl"]').text)
        print('')
        browser.find_element_by_xpath('//button[@data-action="toggle-subscribe-user"]').click()
    except:
        if VERBOSE:
            print('Exception thrown when trying to follow the user.')
        pass


def UnFollowUser(browser):
    """
    UnFollow a just from your followed user list.
    browser: selenium webdriver used to interact with the browser.
    Note: view the black list of users you do not want to unfollow.
    """

    browser.get('https://medium.com/')

    try:
        browser.find_element_by_xpath('//div[@class="avatar"]/img').click()
        time.sleep(3)
        profileUrl = browser.find_element_by_xpath('//a[contains(text(),"Profile")]').get_attribute("href")+'/following'
        browser.get(profileUrl)
        time.sleep(3)
        followedUsers = browser.find_elements_by_xpath('//a[@data-action="show-user-card"]')
        random.shuffle(followedUsers)

        for followedUser in followedUsers:
            followedUserUrl = followedUser.get_attribute("href")
            if not any(blackListUser in followedUserUrl for blackListUser in UNFOLLOW_USERS_BLACK_LIST):
                browser.get(followedUserUrl)
                break

        time.sleep(3)
        print('UnFollow the user: '+browser.find_element_by_xpath('//h1[@class="hero-title"]').text)
        print('')
        browser.find_element_by_xpath('//button[@data-action="toggle-subscribe-user"]').click()

    except:
        if VERBOSE:
            print('Exception thrown when trying to unfollow a user.')
        pass


def ScrollToBottomAndWaitForLoad(browser):
    """
    Scroll to the bottom of the page and wait for the page to perform it's lazy laoding.
    browser: selenium webdriver used to interact with the browser.
    """

    browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(4)


if __name__ == '__main__':
    Launch()
