import tweepy
import praw
from difflib import SequenceMatcher
from datetime import datetime
import time
from itertools import islice 

## Twitter Credentials
TW_CONSUMER_KEY = ""
TW_CONSUMER_SECRET = ""
TW_KEY = ""
TW_SECRET = ""

## Reddit Credentials
# From the Apps page:
RD_CLIENT_ID = ""
RD_CLIENT_SECRET = ""
RD_USERAGENT = ""
# The credentials of the useraccount you wish to post with
RD_USERNAME = ""
RD_PASSWORD = ""
# The subreddit you wish to post to, and the Twitter user you wish to post from
SUBREDDIT = ""
USER_TO_SEARCH = ""


# Initialize Twitter
auth = tweepy.OAuthHandler(TW_CONSUMER_KEY, TW_CONSUMER_SECRET)
auth.set_access_token(TW_KEY, TW_SECRET)
api = tweepy.API(auth)

# Initialize Reddit
reddit = praw.Reddit(client_id=RD_CLIENT_ID, \
					 client_secret=RD_CLIENT_SECRET, \
					 user_agent=RD_USERAGENT, \
					 username=RD_USERNAME, \
					 password=RD_PASSWORD)
reddit.validate_on_submit = True
# Initialize the subreddit
sub = reddit.subreddit(SUBREDDIT)

# Simple checking (see if we have already fetched this tweet)
alreadyFetched = []

# Fetches the newest tweet from the Twitter user
def fetchNewTweet():
	return api.user_timeline(screen_name=USER_TO_SEARCH, tweet_mode="extended", exclude_replies=True)[0]

# Check sif the tweet is a valid one, and posts if it is
def handleTweet():
	newTweet = fetchNewTweet() # Get the new tweet

	# Figure out how long ago this tweet was posted
	postedTime = (datetime.utcnow() - newTweet.created_at).total_seconds() / 60.0
	postedTime = int(postedTime)

	# We don't care about tweets older than 5 minutes (assume we've already handled it OR someone's already posted it by then)
	if postedTime > 5:
		message = "No new tweets (last tweet: {0} minutes ago)".format(postedTime)

	# If we've already taken care of it, do nothing more
	elif newTweet.id in alreadyFetched:
		# Do nothing with it
		message = "Already fetched"

	# It's within 5 minutes and we haven't handled this one yet
	else:
		if checkRedditUnique(newTweet):
			# If we pass this check, that means we are a GO to post
			url = "https://twitter.com/{0}/status/{1}".format(USER_TO_SEARCH, newTweet.id) # Generate the full Tweet url
			sub.submit("[{0}] {1}".format(USER_TO_SEARCH, newTweet.full_text), url=url, resubmit=False)
			message = "Submitted"
		else:
			# Someone beat us to the punch
			message = "Tweet isn't unique (Someone already posted it)"

	# Add to the array so we know it's been handled
	alreadyFetched.append(newTweet.id) 

	# Status message
	message = "{0} ['{1}...']".format(message, newTweet.full_text[:50])
	print(message)

	# Read the newest 100 lines
	with open("main.html", 'r+') as f:
		content = list(islice(f, 100))
		
	# Add the new message 
	with open("main.html", 'w') as f:
		f.write(message + '<br>\n')
		for line in content:
			f.write(line)

def checkRedditUnique(newTweet):
	# Check if the post is unique (ie. we're the first here)
	for submission in sub.new(limit=10):
		# Check if I've already posted it
		user = reddit.redditor(RD_USERNAME)
		for post in user.submissions.new(limit=1):
			# We know what the title would be, so it's easy to check
			if str(newTweet.full_text)[:20] in post.title:
				return False

		# Check for the link (best method if someone else posted)
		if str(newTweet.id) in submission.url:
			return False 

		elif SequenceMatcher(None, newTweet.full_text, submission.title).ratio() > 0.95:
			return False

	return True


while True:
	handleTweet()
	time.sleep(5)