import os
from urllib.parse import urlparse
from urllib.parse import parse_qs
from googleapiclient.discovery import build
import csv


# This function is used to obtain the video id from any kind of input Youtube link
def vid_id(value):
    # urlparse() - parses or splits a URL into six components, returning a 6-item named tuple. 
    # This corresponds to the general structure of a URL: scheme:// netloc / path ; parameters ? query # fragment. 
    # Each tuple item is a string
    query = urlparse(value)
    if query.hostname == 'youtu.be':
        return query.path[1:]
    if query.hostname in ('www.youtube.com', 'youtube.com'):
        if query.path == '/watch':
            # parse_qs() parses a query string given as a string argument 
            # Data are returned as a dictionary. 
            # The dictionary keys are the unique query variable names and the values are lists of values for each name.
            p = parse_qs(query.query)
            return p['v'][0]
        if query.path[:7] == '/embed/':
            return query.path.split('/')[2]
        if query.path[:3] == '/v/':
            return query.path.split('/')[2]
    # fail?
    return None


def main():
    # Disable OAuthlib's HTTPS verification when running locally.
    # *DO NOT* leave this option enabled in production.
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    api_service_name = "youtube"
    api_version = "v3"
    developer_key = "api key"

    youtube = build(api_service_name, api_version, developerKey=developer_key)

    video_link = input('Enter video link: ')  # takes the yt video link as input from user
    video_id = vid_id(video_link)  # extracts and the stores the video id from the link

    field_names = ['Video Id', 'Comment ID', 'Display Name', 'Comment', 'Likes',
                   'No. of Replies']  # headimgs of columns on csv file
    video_id_list = [video_id]
    comments_temp = []  # stores a list of all comments and replies (with suffix "r-")
    comment_id_temp = []  # stores a list of all comment ids
    commenter_name = []  # stores a list of names of commenter
    replycount = []  # stores a list of no. of replies to each comment
    like_count = []  # stores a list of no. of likes on each comment

    nextpage_token = None  # initialize the nextpage token

    # detailed info about commentThreads.list() at https://developers.google.com/youtube/v3/docs/commentThreads/list
    while 1:
        # we generate an API Request with the commentThreads.list() for the YT Data Api 
        # to send a list of comments and replies related to the given video id
        # however the max no. of replies commentThreads.list() can retrun for every individual comment is capped to 5 
        request = youtube.commentThreads().list(part='snippet,replies',
                                                videoId=video_id,
                                                maxResults=100,
                                                order='time',
                                                pageToken=nextpage_token,
                                                textFormat='plainText')
        response = request.execute()  # saves the api's json response as a nested set of dictionaries and lists

        nextpage_token = response.get('nextPageToken')

        for item in response['items']:
            comments_temp.append(item['snippet']['topLevelComment']['snippet']['textDisplay'])
            comment_id_temp.append(item['snippet']['topLevelComment']['id'])
            commenter_name.append(item['snippet']['topLevelComment']['snippet']['authorDisplayName'])
            replycount.append(item['snippet']['totalReplyCount'])
            like_count.append(item['snippet']['topLevelComment']['snippet']['likeCount'])

            # if the reply count for the current comment is less than 5
            if 0 < replycount[-1] <= 5:
                # we iterate through them in our existing response and add them to the list
                for reply in item['replies']['comments']:
                    # add a suffix "r-" to the extracted reply
                    reply_temp = 'r-' + reply['snippet']['textDisplay']

                    # append the reply to the list of comments
                    comments_temp.append(reply_temp)

                    # stores the comment id to which it is a reply (for identification later)
                    comment_id_temp.append(reply['snippet']['parentId'])

                    commenter_name.append(reply['snippet']['authorDisplayName'])
                    replycount.append("NA")
                    like_count.append(reply['snippet']['likeCount'])

            # if the reply count is greater than 5
            elif replycount[-1] > 5:
                nextpage_token2 = None
                while 1:
                    # we generate a new api request, this time with the comments.list() as it returns all the replies
                    # for the specified comment id
                    request2 = youtube.comments().list(part="snippet",
                                                       maxResults=100,
                                                       parentId=comment_id_temp[-1],
                                                       textFormat="plainText")
                    response2 = request2.execute()

                    nextpage_token2 = response2.get('nextPageToken')

                    for item in response2['items']:
                        comments_temp.append('r-' + item['snippet']['textDisplay'])
                        comment_id_temp.append(item['snippet']['parentId'])
                        commenter_name.append(item['snippet']['authorDisplayName'])
                        replycount.append('NA')
                        like_count.append(item['snippet']['likeCount'])

                    if nextpage_token2 is None:
                        break

        if nextpage_token is None:
            break

    video_id_list = video_id_list * len(comment_id_temp)

    # Merges the different columns / lists and stores them row-wise  
    rows = zip(video_id_list, comment_id_temp, commenter_name, comments_temp, like_count, replycount)

    # This open a csv fil
    # if writing to a new csv file reolace 'a' with 'w'
    with open('D:\Coding\Python\Comments.temp.csv', 'w', newline='', encoding='utf-8') as f:
        # create a writer object which will be used to write data into the file
        writer_object = csv.writer(f)

        # loop to write data
        for r in rows:
            writer_object.writerow(r)

    print("Your csv file is stored in the Python folder in the D drive")


if __name__ == "__main__":
    main()
