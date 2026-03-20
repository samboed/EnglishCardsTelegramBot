# EnglishCardsTelegramBot

Telegram bot for learning English words using spaced repetition.

## Overview




## Project Structure

```
EnglishCardsTelegramBot /
├── data/
│   └── collections/ # directory for basic sets of words
│       └── General.csv # basic set of words
├── images/ # photos for README
├── src/
│   ├── logger.py - logger initializer
│   ├── setup_config.py - setting config creator
│   ├── bot/
│   │   ├── bot.py - telegram bot description logic
│   │   ├── defines.py - constants for bot
│   │   ├── collection.py - interaction with collections
│   │   ├── repeat_words.py - repeatition session
│   │   └── service.py - service functions
│   └── db/ 
│       ├── sql/
│       │   └── create_tables.sql - creation database sctructure logic
│       ├── db.py - class of interaction with database
│       ├── activity.py - interaction with UserActivity table
│       ├── collection.py - interaction with collections and words
│       ├── repeat_session.py - interaction with UsersRepeatSession table
│       ├── service.py - database initial functions
│       ├── statistic.py - user statistic get functions
│       ├── user_progress.py - updating user progress
│       └── users.py - interaction with Users table
├── requirements.txt - project requirements
└── README.md
```

## Database Structure

![](images/db_structure.png)

### Tables List:
* *Users* - telegram uid list for each user
* *UserActivity* - registration of user activities
* *UserProgress* - user progress in learned words
* *UserRepeatSession* - table for temporarily storing words during a user's learning session
* *Collections* - collection info
* *CollectionsUsers* - available collections for user
* *CollectionsWords* - listing the russian and english word IDs for each collection
* *RuWords* - list of russian words
* *EnWords* - list of english words

## Setup and Installation
### Python setup

This project depends on Python version 3.12 or higher.

1. Cloning repository

``` git clone https://github.com/samboed/EnglishCardsTelegramBot ``` 

2. Go to the cloned directory

``` cd EnglishCardsTelegramBot ``` 

3. Create virtual environment

``` python -m venv .venv ``` 

4. Activate virtual environment

* Windows (CMD): ```.venv\Scripts\activate.bat```
* Windows (PowerShell): ```.venv\Scripts\Activate.ps1```
* Linux: ```.venv\Scripts\activate```

5. Install requirements

```pip install -r requirements.txt```


### Database installation

This project uses PostgreSQL for data storage.

1. Download installer for your OS system - https://www.postgresql.org/download/ 
2. Install PostgreSQL 
