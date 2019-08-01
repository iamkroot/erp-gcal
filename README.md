# ERP, Google Calendar, Moodle CMS

A script to create Google Calendar events for the entire semester for the courses you've enrolled in. This is mainly inteded for the use of students of [BITS Pilani](http://bits-pilani.ac.in).

## Features
+ Creates detailed calendar events with room and professor information.
+ Events are color-coded according to type (Lecture, Tutorial, Practical, etc.)
+ Includes Midsem and Compre Exam Events too.
+ You can override course sections to set them different from the ones you've registered to.
+ Automatically enrolls you into these courses on Moodle CMS

## Getting started
### Parsing
The app requires the excel version on the pdf given by Timetable Divison. To convert:
1. Extract the main timetable pages from the pdf into another pdf. (You can use a print to pdf service for this).
2. Use [this](https://ilovepdf.com/pdf_to_excel) site to convert to excel.

Follow same steps for midsem schedule, and also, convert the midsem excel to CSV format.

**OR**

You can use the pre-parsed timetable JSON file at [this](https://drive.google.com/drive/folders/1b9GT6G7xyj6Nr9xAfSBJit3rtP3hhd2F?usp=sharing) location (Use BITSmail to log in). I will try to update it every semester, but no guarantees.
NOTE: The timetable changes aren't reflected in the file. You can manually edit the file as necessary.

### Configuration
Config file is in [TOML](https://github.com/toml-lang/toml) format. See [`sample_config.toml`](sample_config.toml). After editing, use [this](http://toml-online-parser.ovonick.com/) site to validate your file.

### Installation
1. Clone the repo to a directory of your choice/click "[Download as zip](https://github.com/iamkroot/erp-gcal-cms/archive/master.zip)" and extract it.
2. Rename the `sample_config.toml` to `config.toml` and set the required values (See [Configuration](#Configuration) section). 
3. Ensure you have [Python 3.6](https://www.python.org/downloads/) or higher installed, and in your system `PATH`.
4. Install `pipenv` using `pip install pipenv`.
5. Inside the downloaded folder, run `pipenv install` in CMD or Terminal.

### Running
Use `pipenv run python main.py` to start the program. During the first run, it will ask you to authorize the app to access you Google Calendar Account. Select your BITS Google Account here. Everything else will be handled by the script.

## Contributing
Feel free to create a new issue in case you find a bug/want to have a feature added. Proper PRs are welcome.

## Authors
+ [Krut Patel](https://github.com/iamkroot)
