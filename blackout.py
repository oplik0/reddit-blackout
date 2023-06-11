"""A simple script for privating subreddits for the blackout on 12th."""

# imports some built in packages:
# os.environ is used to access environmental variables, where we will pass our secrets and variables
# os.remove is used to delete the backup files after they are no longer needed
from os import environ, remove

# os.path.exists is used to check if a file exists, which we will use for mode selection
from os.path import exists

# a module for reading and writing Comma Separated Value (CSV) files - basically, one of the simplest formats for storing data
import csv

# regular expression module - here just used to split a string into a list with whitespace removed
from re import split

# used to run the gh command to disable the workflow after blackout is over
import subprocess

# reddit API wrapper, basically makes connecting to reddit really simple and more readable
# without this one would need to write a lot of code to even log in
import praw

# create a Reddit instance using environment variables for authentication (set in workflow file)
# this will be used to interact with Reddit API
reddit = praw.Reddit(
    # this is the ID of the app we created in the Reddit developer portal
    client_id=environ.get('REDDIT_CLIENT_ID'),
    # this is the secret of the app we created in the Reddit developer portal
    client_secret=environ.get('REDDIT_CLIENT_SECRET'),
    # this is the username of the account we want to delete all content from
    # should be yours otherwise it probably won't work :)
    username=environ.get('REDDIT_USERNAME') or None,
    # this is the password of the account we want to delete all content from
    # unfortunate it is necessary for this authentication method
    password=environ.get('REDDIT_PASSWORD') or None,
    # Reddit Data API terms requires not masking the user agent - but I want this to be configurable in case they find this script and decide to block it
    user_agent=environ.get('REDDIT_USER_AGENT') or "Blackout",
    # alternative authentication method that works with 2FA, but is more complicated to set up
    refresh_token=environ.get('REDDIT_REFRESH_TOKEN') or None
)

def selected_subreddits():
    """Generator that returns all subreddits to be privated."""
    all_moderated = reddit.user.moderator_subreddits()
    # support both blacklisting and whitelisting - note that if both are set, exclusions takes precedence
    excluded = split(r"\s*,\s*", environ.get('SUBREDDIT_BLACKLIST') or "") if environ.get('SUBREDDIT_BLACKLIST') else []
    included = split(r"\s*,\s*", environ.get('SUBREDDIT_WHITELIST') or "") if environ.get('SUBREDDIT_WHITELIST') else []

    for subreddit in all_moderated:
        # skip subreddits that are already private, or are just users
        if subreddit.subreddit_type in ["user", "private"]:
            continue
        if subreddit.display_name in excluded:
            continue
        if not included or subreddit.display_name in included:
            print(f"Including {subreddit.display_name}")
            yield subreddit

def restore_subreddit(name, description, type):
    """Restore a subreddit to its previous state."""
    subreddit = reddit.subreddit(name)
    subreddit.mod.update(
        public_description=description,
        subreddit_type=type
    )

def restore_contributor(subreddit, user):
    """Restore a user to a subreddit's approved submitters list."""
    subreddit = reddit.subreddit(subreddit)
    subreddit.contributor.add(user)

def private_subreddit(subreddit):
    """Set a subreddit to private."""
    # get the current description and type of the subreddit
    old_description = subreddit.public_description
    old_type = subreddit.mod.settings().get("subreddit_type")
    
    # remove all approved users
    for contributor in subreddit.contributor():
        subreddit.contributor.remove(contributor)

    # new description can be set via the environment, or will default to a message about the blackout with relevant links
    new_description = f"/r/{subreddit.display_name} {environ.get('SUBREDDIT_DESCRIPTION') or 'is now private to protest Reddits API pricing changes and the death of 3rd party apps. [Click here to find out why we have gone dark](https://www.theverge.com/2023/6/5/23749188/reddit-subreddit-private-protest-api-changes-apollo-charges). [You can also find a list of other subs that are going dark here](https://reddark.untone.uk/).'}"

    # set the subreddit to private    
    subreddit.mod.update(public_description=new_description,
        subreddit_type="private",
        disable_contributor_requests=True
    )

    # return the old description and type so they can be restored later
    return old_description, old_type

def unschedule():
    """Removes cron triggers from the action"""
    subprocess.run(["gh", "workflow", "disable", "blackout"])
# a function just as good practice - so this can be imported and called from other scripts
def main():
    """Set moderated subreddits to private."""

    # set the mode - if we have a backup file, restore subreddits. Otherwise, private them.
    restore = exists("subreddits.csv") and exists("approved_users.csv")

    if restore:
        print("Restoring subreddits")
        # count the number of subreddits and users restored
        sub_count = 0
        user_count = 0
        with open("subreddits.csv", "r") as subreddits:
            reader = csv.DictReader(subreddits)
            for row in reader:
                sub_count += 1
                restore_subreddit(**row)
        with open("approved_users.csv", "r") as approved_users:
            reader = csv.DictReader(approved_users)
            for row in reader:
                user_count += 1
                restore_contributor(**row)
        print(f"Restored {sub_count} subreddits and {user_count} approved users")
        
        # remove the backup files
        remove("subreddits.csv")
        remove("approved_users.csv")

        # remove the cron triggers from the workflow file
        unschedule()

    else:
        print("Setting subreddits to private")
        # count the number of subreddits privated
        sub_count = 0
        with open("subreddits.csv", "w") as subreddits:
            with open("approved_users.csv", "w") as approved_users:
                subreddits_writer = csv.DictWriter(subreddits, fieldnames=["name", "description", "type"])
                approved_users_writer = csv.DictWriter(approved_users, fieldnames=["subreddit", "user"])
                subreddits_writer.writeheader()
                approved_users_writer.writeheader()
                for subreddit in selected_subreddits():
                    sub_count += 1
                    # backup approved users
                    for contributor in subreddit.contributor():
                        approved_users_writer.writerow({"subreddit": subreddit.display_name,  "user": contributor.name})
                    
                    # set subreddit to private
                    old_description, old_type = private_subreddit(subreddit)

                    # # backup old description and type
                    subreddits_writer.writerow({"name": subreddit.display_name, "description": old_description, "type": old_type})
                    print(f"Privated {subreddit.display_name}")
        print(f"Set {sub_count} subreddits to private")

# runs the main function if the script is called directly (eg. `python3 wipe_reddit_account.py`)
# without this the main method wouldn't run
if __name__ == "__main__":
    main()
