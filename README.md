**Whitelist Bot**

A Discord bot that helps manage whitelisting for your server.

**Features**

* Automatically assigns a role to whitelisted members when they join the server
* Sends a review embed to a designated channel when a new member joins, allowing admins to accept or deny the member
* Allows admins to accept or deny members using buttons on the review embed

**Setup**

1. Clone this repository to your local machine
2. Install the required dependencies using `pip install -r requirements.txt`
3. Create a new Discord bot on the Discord Developer Portal and obtain a bot token
4. Replace the `TOKEN` variable in `bot.py` with your bot token
5. Replace the following IDs in the code with your own IDs:
	* `whitelist_role_id` in `source/modules/whitelist.py` with the ID of the role that you want to assign to whitelisted members
	* `whitelist_channel` in `source/modules/whitelist.py` with the ID of the channel where you want to send review embeds
	* `owner_id` in `bot.py` with your own Discord ID
6. Run the bot using `python bot.py`

**Important**

Make sure to replace the IDs in the code with your own IDs, as mentioned above. This will ensure that the bot works correctly with your server and roles.

**Note**

This bot uses a simple JSON file to store whitelist data. This file is not encrypted, so you should not use this bot to store sensitive information.

I hope this helps! Let me know if you have any questions or need further assistance.