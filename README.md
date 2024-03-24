# lion_bot
This is a [Discord](https://discord.com/) bot that I built specifically for a server I share with my friends. The intent is both to add a little fun to the server and record messages for a little data science.

## Contents
- [Features](#features)
  - [Client Commands](#client-commands)
  - [Event Handling](#event-handling)
  - [Database](#database)
- [Usage](#usage)
  - [help](#help)
  - [ck](#ck)
  - [daily](#daily-1)
  - [debug](#debug)
  - [disconnect](#disconnect)
  - [list](#list)
  - [ping](#ping)
- [How to Contribute](#how-to-contribute)
- [License](#license)

## Features
### Client Commands
This is the most fun and important part of the bot. Users can interact directly with the bot by using the bot's pre-programmed slash commands in any text channel. Begin a message with a forward-slash `/` to see all of the slash commands available to you.

To see what commands *lion-bot* provides and how to use them in Discord, see [Usage](#usage).

### Event Handling
Certain events are handled by the bot asynchronously. The most important event is the `on_message` event, which happens every time a message is sent an any Discord server *lion_bot* is in. *lion_bot* will process each message, record each message in a database (see [Database](#database)), and determine in a response from *lion_bot* is warranted.

Some other, less interesting events that *lion_bot* listens to include:
- `on_connect` is used to inform the bot owner when the bot will begin a log.
- `on_ready` is used to sync client commands with each server and begin the income loop (##############################).
- `on_voice_state_update` is used to inform the bot owner when someone connects to a voice channel.

### Database
*lion_bot* uses a MongoDB database to keep track of several things. This is a list of all database collections, what the contain, and what they are used for.

Using a database allows me to keep important data in an accessible location off of my computer. This is important especially when working on the bot, as the bot can be running on two separate computers while using the same set of data.

#### posts
Contains Discord message content and metadata. This is kept in the database for both a fun future data science project and potential use cases to enhance the bot.

Recently I discovered that Discord only allows 50 pinned messages per channel. I also want to use this database of messages to save messages that would otherwise have been lost.

#### daily
Contains the last time a user used the `/daily` command. Storing this in the database ensures that users cannot use `/daily` more often than intended even while the bot is under maintenance.

#### the_list
Literally contains a list of members. Can be added to using `/list`. What the list does is secret :^)

#### members
Contains all information related to the `/ck` command.

## Usage
This is a list of commands *lion_bot* provides, how to use them, and what they do.

Here is how to read commands from this section:
- `/command` is the command that can be typed as-is in Discord.
- `/command subcommand` is the command and following subcommand that can also be typed as-is in Discord.
- `/command [subcommand1|subcommand2]` indicates that there are two possible options for subcommand. Either subcommand may be typed into Discord ***without*** square brackets `[]` or a pipe `|`.
- `/command [ARGUMENT]` indicates that you are *expected* to type something (anything) as a command argument, and that argument will be read by the bot as-is.
  - For example, when using `/ck enroll [NAME]` I might type `/ck enroll Lion` in to Discord.

### `/help`
Usage: `/help` \
Shows usage information for all of *lion_bot*'s commands.

### `/ck`
Usage: `/ck [help|enroll|stats|update]` \
[Crusader Kings](https://store.steampowered.com/app/1158310/Crusader_Kings_III/)-style roleplay.

#### - `/ck help`
Shows usage information for `/ck`.

#### - `/ck enroll [NAME]`
Enroll yourself into the Crusader Kings roleplay. Required before using other subcommands.

#### - `/ck stats [@NAME]`
Check the resources and statistics of yourself or another CK-enrolled user. `[@NAME]` is *optional*. If left empty, this will display your own stats. If you ping another user, it will display their stats.

#### - `/ck update [name|title|disposition] [NEW]`
Update your own CK information with whatever you type for `[NEW]`. 

### `/daily`
Usage: `/daily` \
Rolls a d100. You may win a prize if you roll high enough!

### `/debug`
Intended for the bot owner only.

### `/disconnect`
Usage: `/disconnect [@NAME]` \
Disconnects the specified user from their voice channel.

### `/list`
Usage: `/list add [@NAME]`
Adds the specified user to **THE LIST**. Command is only usable by users with the proper permissions.

### `/ping`
Usage: `/ping` \
Tests the latency of the bot's server

## How to Contribute
Bug reports and pull requsts are welcomed on Github! You can help by [creating an issue](https://github.com/Lion4567714/lion_bot/issues)!

## License
MIT License, Copyright (c) 2024 Anders Gilliland
