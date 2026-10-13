"""Объектная модель предметной области «Расписание занятий»."""

from models.base import Entity
from models.lesson import DAYS, Lesson
from models.room import Room
from models.schedule import Schedule
from models.teacher import Teacher

__all__ = ["DAYS", "Entity", "Lesson", "Room", "Schedule", "Teacher"]
