from abc import ABC, abstractclassmethod
from models import *
from utils.exception import *
from bs4 import BeautifulSoup
from bs4.element import Tag
from config.booking_conf import booking_conf

class AbstractScraper(ABC):
    
    @abstractclassmethod
    def get_general_info(self) -> Hotel:
        ''' Get general info'''
        
    @abstractclassmethod
    def get_rating(self) -> HotelRating:
        ''' Get rating'''
        
    @abstractclassmethod    
    def get_review_info(self) -> HotelReview:
        ''' Get review info'''
        
    @abstractclassmethod    
    def get_rooms(self) -> HotelRoomComposition:
        ''' Get description'''



class BookingScraper(AbstractScraper):
    body: Tag 
    scraper_status: ScraperException
    hotel: Hotel
    
    def __init__(self, content: BeautifulSoup):
        try:
            self.body = content.find(id='bodyconstraint')
            self.scraper_status = ScraperException(200, 'OK')
        except Exception as _ex:
            print(_ex)
            self.scraper_status = ScraperException(
                status_code=404,
                message="Body Not Found"
            )
        
    def get_general_info(self) -> Hotel:
        
        hotel_name = self.body.find_all(class_=booking_conf['hotel_name'])
        hotel_address = self.body.find_all(class_=booking_conf['hotel_address'])
        hotel_description = self.body.find_all(class_=booking_conf['description'])
        
        if not hotel_name:
            hotel_name = [ScraperValueException('Hotel Name')]
        if not hotel_address:
            hotel_address = [ScraperValueException('Hotel Address')]
        if not hotel_description:
            hotel_description = [ScraperValueException('Hotel Description')]
        
        hotel = Hotel(
            name=hotel_name[0].get_text(),
            address=hotel_address[0].get_text(),
            description=hotel_description[0].get_text()
        )
        self.hotel = hotel
        return hotel
        
    def get_rating(self) -> HotelRating:
        rating_block = self.body.find_all(
            class_=booking_conf['rating']['block']
        )
        if rating_block:
            rating = rating_block[0]
            point_type = booking_conf['rating']['point_type']
            
            rating_score = len(rating.find_all(class_=booking_conf['rating']['points']))    
        
            classification_class = rating.find_all(
                class_=point_type['class'])
            
            if not classification_class:
                classification_name = ScraperValueException('Classification Name').get_text()
            else:
                classification_name = point_type['types'][classification_class[0][point_type['identificator']]]
            
            hotel_rating = HotelRating(
                classification=classification_name,
                rating=int(rating_score)
            )
            self.hotel.rating = hotel_rating
            return ScraperException(200, 'OK'), self.hotel
        else:
            self.hotel.rating = None
            return ScraperException(404, 'Rating Not Found'), self.hotel
        
        
    def get_review_info(self) -> HotelReview:
        review_block = self.body.find_all(
            class_=booking_conf['review']['review_block']
        )
        if review_block:
            review_block = review_block[0]
            review_conf = booking_conf['review']
            
            review_score = review_block.find_all(class_=review_conf['review_score'])
            count_reviews = review_block.find_all(class_=review_conf['count_reviews'])
            review_name = review_block.find_all(class_=review_conf['review_name'])
            
            if not review_score:
                review_score = [ScraperValueException('Review Score')]
            if not count_reviews:
                count_reviews = [ScraperValueException('Count Review')]
            if not review_name:
                review_name = [ScraperValueException('Review Name')]
                
            hotel_review = HotelReview(
                review_count=count_reviews[0].get_text(),
                review_name=review_name[0].get_text(),
                review_point=review_score[0].get_text()
            )
            self.hotel.review = hotel_review
            return ScraperException(200, 'OK'), self.hotel
        else:
            self.hotel.review = None
            return ScraperException(404, 'Review Not Found'), self.hotel
        
    def get_rooms(self) -> HotelRoomComposition:
        room_conf = booking_conf['room']
        room_block = self.body.find_all(
            class_=room_conf['room_block']
        )
        if room_block:
            rooms_list = list()
            rooms = room_block[0].find_all(class_=room_conf['room_element'])
            if rooms:
                for room in rooms[room_conf['start_from']:]:
                    room_type = room.find_all(class_=room_conf['room_type'])
                    
                    if not room_type:
                        room_type = [ScraperValueException('Room Type')]
                        
                    room_obj = HotelRoom(
                        r_type=room_type[0].get_text()
                    )
                    rooms_list.append(room_obj)
                
                rooms = HotelRoomComposition()
                rooms.extend(rooms_list)
            self.hotel.rooms = rooms
            return ScraperException(200, 'OK'), self.hotel
        else:
            self.hotel.rooms = None
            return ScraperException(404, 'Rooms Not Found'), self.hotel
        
    def get_other_hotel(self):
        other_hotel_conf = booking_conf['alternative_hotels']
        other_hotel_block = self.body.find_all(
            class_=other_hotel_conf['block']
        )
        if other_hotel_block:
            hotel_list = other_hotel_block[0].find_all(class_=other_hotel_conf['list'])
            if hotel_list:
                for hotel in hotel_list:
                    hotel_el = hotel.find_all(class_=other_hotel_conf['title'])
                    if not hotel_el or hotel_el[0].get_text() == '':
                        hotel_el = [ScraperValueException('Other Hotel')]
                    self.hotel.add_other_hotel(hotel_el[0].get_text())
                    
            return ScraperException(200, 'OK'), self.hotel
        else:
            self.hotel.other_hotel = []
            return ScraperException(404, 'Other Hotel Not Found'), self.hotel
        
    # TODO: make calling functions dynamic
    def __call__(self):
        if self.scraper_status.status_code == 404:
            return self.scraper_status
        
        hotel = self.get_general_info()
        status, hotel = self.get_rating()
        status, hotel = self.get_review_info()
        status, hotel = self.get_rooms()
        status, hotel = self.get_other_hotel()
        
        return status, hotel
    