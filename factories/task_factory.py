from tasks.models import Task


class TaskFactory:

    @staticmethod
    def create_task(title, description, user):
        """
        Factory method to create Task objects
        """
        return Task.objects.create(
            title=title,
            description=description,
            user=user
        )
