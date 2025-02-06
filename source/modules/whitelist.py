import discord, json
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button

class ReviewButton(Button):
    def __init__(self, label, style, custom_id, member):
        super().__init__(label=label, style=style, custom_id=custom_id)
        self.member = member

    async def callback(self, interaction: discord.Interaction):
        if self.custom_id == "accept":
            whitelist_role = interaction.guild.get_role(self.view.whitelist_role_id)
            await self.member.add_roles(whitelist_role)
            await interaction.response.defer()
            await interaction.followup.send(f"Accepted {self.member.mention} and added to whitelist")
        elif self.custom_id == "deny":
            try:
                await self.member.send("You have been denied access to this server. You will be banned shortly.")
            except discord.Forbidden:
                await interaction.response.defer()
                await interaction.followup.send(f"Failed to send message to {self.member.mention}. Banning anyway.")
            await self.member.ban(reason="Denied by admin")
            await interaction.response.defer()
            await interaction.followup.send(f"Denied {self.member.mention} and banned from the server")

class ReviewView(View):
    def __init__(self, whitelist_role_id, member):
        super().__init__()
        self.whitelist_role_id = whitelist_role_id
        self.member = member
        self.add_item(ReviewButton("Accept", discord.ButtonStyle.green, "accept", member))
        self.add_item(ReviewButton("Deny", discord.ButtonStyle.red, "deny", member))

class Whitelist(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.whitelist_role_id = 1336950517099790389 # Replace with your role ID
        self.whitelist_channel = 1336950948182097971 # Replace with your whitelist feed channel ID
        self.whitelist_log_file = "whitelist_log.json"

    whitelist_group = app_commands.Group(name="whitelist", description="Manage the whitelist")

    @whitelist_group.command(name="deny")
    @app_commands.checks.has_permissions(administrator=True)
    async def whitelist_deny(self, interaction: discord.Interaction, user: discord.Member):
        """Deny a user who has joined the server"""
        try:
            await user.send("You have been denied access to this server. You will be banned shortly.")
        except discord.Forbidden:
            await interaction.response.send_message(f"Failed to send message to {user.mention}. Banning anyway.", ephemeral=True)
        
        await user.ban(reason="Denied by admin")
        await interaction.response.send_message(f"Denied {user.mention} and banned from the server", ephemeral=True)

    @whitelist_group.command(name="accept")
    @app_commands.checks.has_permissions(administrator=True)
    async def whitelist_accept(self, interaction: discord.Interaction, user: discord.Member):
        """Accept a user who has joined the server"""
        whitelist_role = interaction.guild.get_role(self.whitelist_role_id)
        if whitelist_role in user.roles:
            await interaction.response.send_message(f"{user.mention} is already in the whitelist", ephemeral=True)
            return

        await user.add_roles(whitelist_role)
        await self.log_whitelist_user(user)
        await interaction.response.send_message(f"Accepted {user.mention} and added to whitelist", ephemeral=True)

    async def log_whitelist_user(self, user: discord.Member):
        try:
            with open(self.whitelist_log_file, "r+") as f:
                whitelist_log = json.load(f)
        except FileNotFoundError:
            whitelist_log = []

        whitelist_log.append({
            "user_id": user.id,
            "username": user.name,
            "discriminator": user.discriminator,
            "timestamp": discord.utils.format_dt(discord.utils.utcnow())
        })

        with open(self.whitelist_log_file, "w") as f:
            json.dump(whitelist_log, f, indent=4)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        whitelist_role = member.guild.get_role(self.whitelist_role_id)
        if whitelist_role in member.roles:
            return

        try:
            with open(self.whitelist_log_file, "r") as f:
                whitelist_log = json.load(f)
        except FileNotFoundError:
            whitelist_log = []

        for log_entry in whitelist_log:
            if log_entry["user_id"] == member.id:
                await member.add_roles(whitelist_role)
                return

        review_channel = self.bot.get_channel(self.whitelist_channel)
        embed = discord.Embed(title="New Member Joined", description=f"{member.mention} has joined the server")
        embed.set_thumbnail(url=member.display_avatar)
        embed.add_field(name="Username", value=member.name, inline=False)
        embed.add_field(name="ID", value=member.id, inline=False)
        embed.add_field(name="Joined At", value=member.joined_at.strftime("%Y-%m-%d %H:%M:%S"), inline=False)
        view = ReviewView(self.whitelist_role_id, member)
        await review_channel.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(Whitelist(bot))