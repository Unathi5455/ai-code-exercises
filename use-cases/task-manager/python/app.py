# task_manager/app.py

import argparse
from datetime import datetime, timedelta
from .models import Task, TaskPriority, TaskStatus
from .storage import TaskStorage


class TaskManager:
    """
    TaskManager acts as the core business logic layer of the Task Manager application.

    It is responsible for:
    - Creating tasks
    - Listing and filtering tasks
    - Updating task attributes (status, priority, due date, tags)
    - Deleting tasks
    - Generating task statistics

    It interacts with TaskStorage for persistence and Task model for data representation.
    """

    def __init__(self, storage_path="tasks.json"):
        """
        Initializes the TaskManager with a storage backend.

        Args:
            storage_path (str): Path to the JSON file used for storing tasks.
        """
        self.storage = TaskStorage(storage_path)

    def create_task(self, title, description="", priority_value=2,
                   due_date_str=None, tags=None):
        """
        Creates a new task and stores it.

        Args:
            title (str): Task title
            description (str): Optional task description
            priority_value (int): Priority level (1=LOW to 4=URGENT)
            due_date_str (str): Optional due date in YYYY-MM-DD format
            tags (list): Optional list of tags

        Returns:
            str or None: Task ID if creation is successful, otherwise None

        Notes:
            - Converts priority integer into TaskPriority Enum
            - Converts due date string into datetime object
            - Returns None if due date format is invalid
        """
        priority = TaskPriority(priority_value)
        due_date = None

        if due_date_str:
            try:
                due_date = datetime.strptime(due_date_str, "%Y-%m-%d")
            except ValueError:
                print("Invalid date format. Use YYYY-MM-DD")
                return None

        task = Task(title, description, priority, due_date, tags)
        task_id = self.storage.add_task(task)
        return task_id

    def list_tasks(self, status_filter=None, priority_filter=None, show_overdue=False):
        """
        Retrieves tasks with optional filtering.

        Args:
            status_filter (str): Filter tasks by status
            priority_filter (int): Filter tasks by priority
            show_overdue (bool): If True, returns only overdue tasks

        Returns:
            list: List of Task objects matching filters
        """
        if show_overdue:
            return self.storage.get_overdue_tasks()

        if status_filter:
            status = TaskStatus(status_filter)
            return self.storage.get_tasks_by_status(status)

        if priority_filter:
            priority = TaskPriority(priority_filter)
            return self.storage.get_tasks_by_priority(priority)

        return self.storage.get_all_tasks()

    def update_task_status(self, task_id, new_status_value):
        """
        Updates the status of a task.

        Args:
            task_id (str): ID of the task
            new_status_value (str): New status value

        Returns:
            bool: True if update succeeds, False otherwise

        Notes:
            - If status is DONE, mark_as_done() is used to update timestamps
            - Otherwise, status is updated directly via storage
        """
        new_status = TaskStatus(new_status_value)

        if new_status == TaskStatus.DONE:
            task = self.storage.get_task(task_id)
            if task:
                task.mark_as_done()
                self.storage.save()
                return True
        else:
            return self.storage.update_task(task_id, status=new_status)

    def update_task_priority(self, task_id, new_priority_value):
        """
        Updates the priority of a task.

        Args:
            task_id (str): Task identifier
            new_priority_value (int): New priority level

        Returns:
            bool: Success status
        """
        new_priority = TaskPriority(new_priority_value)
        return self.storage.update_task(task_id, priority=new_priority)

    def update_task_due_date(self, task_id, due_date_str):
        """
        Updates the due date of a task.

        Args:
            task_id (str): Task identifier
            due_date_str (str): New due date (YYYY-MM-DD)

        Returns:
            bool: True if update succeeds, False otherwise

        Notes:
            Prints error message if date format is invalid.
        """
        try:
            due_date = datetime.strptime(due_date_str, "%Y-%m-%d")
            return self.storage.update_task(task_id, due_date=due_date)
        except ValueError:
            print("Invalid date format. Use YYYY-MM-DD")
            return False

    def delete_task(self, task_id):
        """
        Deletes a task from storage.

        Args:
            task_id (str): Task identifier

        Returns:
            bool: True if task was deleted, False otherwise
        """
        return self.storage.delete_task(task_id)

    def get_task_details(self, task_id):
        """
        Retrieves a single task by ID.

        Args:
            task_id (str): Task identifier

        Returns:
            Task or None: Task object if found, otherwise None
        """
        return self.storage.get_task(task_id)

    def add_tag_to_task(self, task_id, tag):
        """
        Adds a tag to a task if it does not already exist.

        Args:
            task_id (str): Task identifier
            tag (str): Tag to add

        Returns:
            bool: True if operation succeeds, False otherwise
        """
        task = self.storage.get_task(task_id)
        if task:
            if tag not in task.tags:
                task.tags.append(tag)
                self.storage.save()
            return True
        return False

    def remove_tag_from_task(self, task_id, tag):
        """
        Removes a tag from a task.

        Args:
            task_id (str): Task identifier
            tag (str): Tag to remove

        Returns:
            bool: True if tag removed successfully, False otherwise
        """
        task = self.storage.get_task(task_id)
        if task and tag in task.tags:
            task.tags.remove(tag)
            self.storage.save()
            return True
        return False

    def get_statistics(self):
        """
        Generates summary statistics for all tasks.

        Returns:
            dict: Contains:
                - total (int): Total number of tasks
                - by_status (dict): Count of tasks per status
                - by_priority (dict): Count of tasks per priority
                - overdue (int): Number of overdue tasks
                - completed_last_week (int): Tasks completed in last 7 days
        """
        tasks = self.storage.get_all_tasks()
        total = len(tasks)

        status_counts = {status.value: 0 for status in TaskStatus}
        for task in tasks:
            status_counts[task.status.value] += 1

        priority_counts = {priority.value: 0 for priority in TaskPriority}
        for task in tasks:
            priority_counts[task.priority.value] += 1

        overdue_count = len([task for task in tasks if task.is_overdue()])

        seven_days_ago = datetime.now() - timedelta(days=7)
        completed_recently = len([
            task for task in tasks
            if task.completed_at and task.completed_at >= seven_days_ago
        ])

        return {
            "total": total,
            "by_status": status_counts,
            "by_priority": priority_counts,
            "overdue": overdue_count,
            "completed_last_week": completed_recently
        }