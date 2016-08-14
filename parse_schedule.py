from BeautifulSoup import BeautifulSoup
from datetime import date, datetime
import argparse
import json
import logging
import pytz
import sys


def session_title(session):
    return session.find('h1', {"class": "title"}).contents[0]


def parse_time(time_string):
    time_format = "%I:%M %p"
    return datetime.strptime(time_string, time_format).time()


def session_start_time(session):
    return parse_time(
        session.find('span', {"class": "start-time"}).contents[0]
    )


def session_end_time(session):
    return parse_time(
        session.find('span', {"class": "end-time"}).contents[0][9:]
    )


def session_speaker_name(session):
    return session.find('p', {"class": "speaker"}).contents[0]


def session_speaker_bio(session):
    name = session_speaker_name(session)
    bio = session.find('div', {"class": "bio"}) or \
        session.find('div', {"class": "bio no-image"})
    if bio is not None:
        bio_paragraphs = [p.contents[0] for p in bio.findAll('p')
                          if len(p.contents) > 0]
        about = "About the speaker:"
        if about in bio_paragraphs:
            bio_paragraphs.remove(about)

        if len(bio_paragraphs) == 0:
            logging.info(u'{} does not have a bio'.format(name))
            return None
        if len(bio_paragraphs) > 1:
            logging.info(u'{} has more than 1 paragraph of bio'.format(name))
            return bio_paragraphs
        return bio_paragraphs[0]

    else:
        logging.info(u'{} does not have a bio'.format(name))
        return None


def session_speaker_photo(session):
    base_url = 'http://abstractions.io'
    bio = session.find('div', {"class": "bio"})
    if bio is not None:
        rel_url = bio.find('img')['src']
        if 'null' not in rel_url:
            return base_url + rel_url

    name = session_speaker_name(session)
    logging.info(u'Speaker {} does not have a photo'.format(name))
    return None


def session_description(session):
    info = session.find('div', {'class': 'information'})
    paragraphs = [p.text for p in info.findChildren() if p.text]
    assert len(paragraphs) == 1
    return paragraphs[0]


def session_location(session):
    return session.find('p', {"class": "time"}).contents[2][2:]


def session_soup_to_dict(session):
    return {
        "title": session_title(session),
        "start_time": session_start_time(session),
        "end_time": session_end_time(session),
        "speaker": {
            "name": session_speaker_name(session),
            "bio": session_speaker_bio(session),
            "photo": session_speaker_photo(session),
        },
        "description": session_description(session),
        "location": session_location(session),
    }


def combine_date_with_session_time(date, time):
    time_zone = pytz.timezone('US/Eastern')
    combined_datetime = time_zone.localize(
        datetime.combine(date, time)
    )
    return combined_datetime.isoformat('T')


def update_session_with_date(session, date):
    session["start_time"] = combine_date_with_session_time(
        date,
        session["start_time"]
    )

    session["end_time"] = combine_date_with_session_time(
        date,
        session["end_time"]
    )

    return session


def update_sessions_with_date(sessions, date):
    return [update_session_with_date(session, date)
            for session in sessions]


def find_sessions(soup):
    return soup.findAll('div', {"class": "session-modal"})


def find_days(soup):
    days = ['Thursday', 'Friday', 'Saturday']
    return {
        day: soup.find('div', id=day)
        for day in days
    }


def parse_sessions(soup):
    sessions = find_sessions(soup)
    return [session_soup_to_dict(session) for session in sessions]


def parse_days(soup):
    sessions_by_day = {
        day: parse_sessions(day_soup)
        for day, day_soup in find_days(soup).iteritems()
    }
    thursday_sessions = update_sessions_with_date(
        sessions_by_day['Thursday'],
        date(2016, 8, 18)
    )
    friday_sessions = update_sessions_with_date(
        sessions_by_day['Friday'],
        date(2016, 8, 19)
    )
    saturday_sessions = update_sessions_with_date(
        sessions_by_day['Saturday'],
        date(2016, 8, 20)
    )
    return thursday_sessions + friday_sessions + saturday_sessions


def parse_args():
    description = ('Convert the schedule HTML into JSON.')
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('schedule', help='Path to the HTML file')
    parser.add_argument('--verbose', '-v', action='count',
                        help='Log more details. Only one level currently.')
    return parser.parse_args()


def main():
    args = parse_args()
    if args.verbose > 0:
        logging.basicConfig(level=logging.DEBUG)
    with open(args.schedule) as f:
        schedule_html = f.read()
    soup = BeautifulSoup(schedule_html)
    sessions = parse_days(soup)
    print(json.dumps(sessions, sort_keys=True, indent=2))


if __name__ == "__main__":
    status = main()
    sys.exit(status)
