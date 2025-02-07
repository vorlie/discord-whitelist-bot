import discord
import json
import logging
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button
import datetime

# Configure logging:  Sets up basic logging to the console.  You can adjust the
# level (e.g., logging.DEBUG, logging.WARNING) to control the verbosity of the
# logs.  The format string specifies how log messages are structured.
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


# ReviewButton Class: Represents a button in the review process (Accept or Deny).
class ReviewButton(Button):
    # __init__:  Initializes the button with a label, style, custom ID, and the
    # member it's associated with.
    def __init__(self, label, style, custom_id, member):
        super().__init__(label=label, style=style, custom_id=custom_id)
        self.member = member  # The Discord member this button is for.

    # callback:  This is the function that's called when the button is pressed.
    # It checks the custom ID to determine whether to accept or deny the user.
    async def callback(self, interaction: discord.Interaction):
        # If the button is the "accept" button, call the accept_user method from
        # the Whitelist cog.
        if self.custom_id == "accept":
            await self.view.cog.accept_user(interaction, self.member)
        # If the button is the "deny" button, call the deny_user method from the
        # Whitelist cog.
        elif self.custom_id == "deny":
            await self.view.cog.deny_user(interaction, self.member)


# ReviewView Class: Represents the view containing the Accept and Deny buttons.
class ReviewView(View):
    # __init__: Initializes the view with the whitelist role ID, the member being
    # reviewed, and a reference to the Whitelist cog.
    def __init__(self, whitelist_role_id, member, cog):
        super().__init__()
        self.whitelist_role_id = whitelist_role_id  # The ID of the whitelist role.
        self.member = member  # The Discord member being reviewed.
        self.cog = cog  # Reference to the Whitelist cog, allowing access to its methods.
        # Add the Accept and Deny buttons to the view.
        self.add_item(
            ReviewButton("Accept", discord.ButtonStyle.green, "accept", member)
        )
        self.add_item(ReviewButton("Deny", discord.ButtonStyle.red, "deny", member))


# Whitelist Class:  This is the main cog that handles the whitelist functionality.
class Whitelist(commands.Cog):
    # __init__: Initializes the cog with the bot instance and configuration
    # settings.
    def __init__(self, bot):
        self.bot = bot  # The Discord bot instance.
        # Replace with your actual whitelist role ID.  This is the role that will
        # be assigned to whitelisted users.
        self.whitelist_role_id = 1336950517099790389
        # Replace with your actual whitelist channel ID.  This is the channel
        # where new member join requests will be sent.
        self.whitelist_channel = 1336950948182097971
        self.whitelist_log_file = (
            "whitelist_log.json"  # The file where whitelist logs are stored.
        )

    # whitelist_group: Creates a slash command group named "whitelist" for
    # managing whitelist commands.
    whitelist_group = app_commands.Group(
        name="whitelist", description="Manage the whitelist"
    )

    # deny_user:  A helper function that denies a user and bans them from the
    # server.  It attempts to send a DM to the user before banning, but proceeds
    # with the ban even if the DM fails (e.g., if the user has DMs disabled).
    async def deny_user(self, interaction: discord.Interaction, user: discord.Member):
        """Denies a user and bans them from the server, even if DMs are closed."""
        try:
            await user.send(
                "You have been denied access to this server. You will be banned shortly."
            )
            logging.info(f"Successfully sent DM to user {user.id} before banning.")
        except discord.Forbidden:
            # Log a warning if the bot can't send a DM (likely due to the user's
            # privacy settings).
            logging.warning(
                f"Failed to send DM to user {user.id} (DMs closed or user blocked bot), proceeding with ban."
            )
            await interaction.followup.send(
                f"Failed to send message to {user.mention} (DMs closed). Banning anyway.",
                ephemeral=True,
            )
        except Exception as e:
            # Log any other exceptions that occur while trying to send the DM.
            logging.exception(f"Error sending DM to user {user.id}: {e}")
            await interaction.followup.send(
                f"An error occurred while trying to message {user.mention}. Banning anyway.",
                ephemeral=True,
            )

        # Proceed with the ban regardless of DM status
        try:
            await user.ban(reason="Denied by admin")
            await interaction.followup.send(
                f"Denied {user.mention} and banned from the server", ephemeral=True
            )
            logging.info(f"Successfully banned user {user.id}.")
        except discord.Forbidden:
            # Log an error if the bot doesn't have permission to ban the user.
            logging.error(f"Failed to ban user {user.id}")
            await interaction.followup.send(
                f"Failed to ban {user.mention}. Insufficient permissions.", ephemeral=True
            )
        except Exception as e:
            # Log any other exceptions that occur while trying to ban the user.
            logging.exception(f"Error banning user {user.id}: {e}")
            await interaction.followup.send(
                f"An error occurred while trying to ban {user.mention}.", ephemeral=True
            )

    # accept_user: A helper function that accepts a user and adds them to the
    # whitelist role.
    async def accept_user(self, interaction: discord.Interaction, user: discord.Member):
        """Accepts a user and adds them to the whitelist."""
        whitelist_role = interaction.guild.get_role(self.whitelist_role_id)
        # Check if the whitelist role exists.
        if not whitelist_role:
            await interaction.followup.send(
                "Whitelist role not found.  Check configuration.", ephemeral=True
            )
            return

        # Check if the user already has the whitelist role.
        if whitelist_role in user.roles:
            await interaction.followup.send(
                f"{user.mention} is already in the whitelist", ephemeral=True
            )
            return

        try:
            await user.add_roles(whitelist_role)  # Add the whitelist role to the user.
            await self.log_whitelist_user(user)  # Log the whitelisting action.
            await interaction.followup.send(
                f"Accepted {user.mention} and added to whitelist", ephemeral=True
            )
        except discord.Forbidden:
            # Log an error if the bot doesn't have permission to add the role.
            logging.error(f"Failed to add role to user {user.id}")
            await interaction.followup.send(
                f"Failed to add whitelist role to {user.mention}. Insufficient permissions.",
                ephemeral=True,
            )
        except Exception as e:
            # Log any other exceptions that occur while trying to add the role.
            logging.exception(f"Error adding role to user {user.id}: {e}")
            await interaction.followup.send(
                f"An error occurred while trying to add the whitelist role to {user.mention}.",
                ephemeral=True,
            )

    # whitelist_deny: A slash command that denies a user.  It can only be used
    # by users with administrator permissions.
    @whitelist_group.command(name="deny")
    @app_commands.checks.has_permissions(administrator=True)
    async def whitelist_deny(
        self, interaction: discord.Interaction, user: discord.Member
    ):
        """Deny a user who has joined the server"""
        # Defer the interaction immediately to prevent timeouts.
        await interaction.response.defer(ephemeral=True)
        await self.deny_user(interaction, user)  # Call the deny_user helper function.

    # whitelist_accept: A slash command that accepts a user.  It can only be used
    # by users with administrator permissions.
    @whitelist_group.command(name="accept")
    @app_commands.checks.has_permissions(administrator=True)
    async def whitelist_accept(
        self, interaction: discord.Interaction, user: discord.Member
    ):
        """Accept a user who has joined the server"""
        # Defer the interaction immediately to prevent timeouts.
        await interaction.response.defer(ephemeral=True)
        # Call the accept_user helper function.
        await self.accept_user(interaction, user)

    # load_whitelist_log: Loads the whitelist log from the JSON file.
    async def load_whitelist_log(self):
        """Loads the whitelist log from file."""
        try:
            with open(self.whitelist_log_file, "r") as f:
                return json.load(f)  # Load the JSON data from the file.
        except FileNotFoundError:
            return []  # Return an empty list if the file doesn't exist.
        except json.JSONDecodeError:
            # Log an error if the JSON file is corrupted.
            logging.error(
                f"Error decoding JSON from {self.whitelist_log_file}.  Returning empty list."
            )
            return []  # Return empty list to avoid errors

    # log_whitelist_user: Logs a whitelisted user to the whitelist log file.
    async def log_whitelist_user(self, user: discord.Member):
        """Logs a whitelisted user to the whitelist log file."""
        whitelist_log = await self.load_whitelist_log()  # Load the existing log.

        # Append the new user's information to the log.
        whitelist_log.append(
            {
                "user_id": user.id,
                "username": user.name,
                "discriminator": user.discriminator,
                "timestamp": datetime.datetime.now().isoformat(),  # Store as ISO 8601
            }
        )

        try:
            with open(self.whitelist_log_file, "w") as f:
                json.dump(whitelist_log, f, indent=4)  # Write the updated log to the file.
        except Exception as e:
            # Log an error if writing to the log file fails.
            logging.error(f"Error writing to whitelist log file: {e}")

    # on_member_join: This event listener is triggered when a new member joins the
    # server.
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Handles new members joining the server."""
        whitelist_role = member.guild.get_role(self.whitelist_role_id)
        # Check if the whitelist role exists.
        if not whitelist_role:
            logging.error("Whitelist role not found. Check configuration.")
            return

        # If the member already has the whitelist role, do nothing.
        if whitelist_role in member.roles:
            return

        whitelist_log = await self.load_whitelist_log()  # Load the whitelist log.

        # Check if the user is already in the whitelist log (e.g., if they left
        # and rejoined).
        for log_entry in whitelist_log:
            if log_entry["user_id"] == member.id:
                try:
                    await member.add_roles(
                        whitelist_role
                    )  # Add the whitelist role to the user.
                    logging.info(
                        f"Automatically whitelisted user {member.id} from log."
                    )
                    return  # Exit after auto-whitelisting
                except discord.Forbidden:
                    # Log an error if the bot doesn't have permission to add the role.
                    logging.error(
                        f"Failed to add role to user {member.id} during auto-whitelist."
                    )
                    return
                except Exception as e:
                    # Log any other exceptions that occur while trying to add the role.
                    logging.exception(f"Error adding role during auto-whitelist: {e}")
                    return

        # If the user is not in the whitelist log, send a message to the review
        # channel with the Accept and Deny buttons.
        review_channel = self.bot.get_channel(self.whitelist_channel)
        # Check if the review channel exists.
        if not review_channel:
            logging.error("Whitelist channel not found. Check configuration.")
            return

        # Create an embed with information about the new member.
        embed = discord.Embed(
            title="New Member Joined", description=f"{member.mention} has joined the server"
        )
        embed.set_thumbnail(url=member.display_avatar)
        embed.add_field(name="Username", value=member.name, inline=False)
        embed.add_field(name="ID", value=member.id, inline=False)
        embed.add_field(
            name="Joined At", value=member.joined_at.strftime("%Y-%m-%d %H:%M:%S"), inline=False
        )
        # Create the ReviewView with the Accept and Deny buttons.
        view = ReviewView(
            self.whitelist_role_id, member, self
        )  # Pass self to ReviewView
        await review_channel.send(
            embed=embed, view=view
        )  # Send the embed and view to the review channel.


# setup: This function is required for all cogs.  It's called when the cog is
# loaded.
async def setup(bot):
    await bot.add_cog(Whitelist(bot))  # Add the Whitelist cog to the bot.
