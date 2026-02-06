from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication

from django.contrib.auth.models import User as DjangoUser

from .models import User, Task
from .serializers import UserSerializer, TaskSerializer
from .permissions import IsTaskAssignee

from singletons.logger_singleton import LoggerSingleton
from factories.task_factory import TaskFactory   # ✅ FACTORY IMPORT


# ============================
# LOGGER (SINGLETON)
# ============================

logger = LoggerSingleton().get_logger()


# ============================
# USERS (SECURED + PASSWORD HASHING)
# ============================

class UserListCreate(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)

        logger.info("User list accessed")

        return Response(serializer.data)

    def post(self, request):
        serializer = UserSerializer(data=request.data)

        if serializer.is_valid():
            data = serializer.validated_data

            # Create Django auth user (password hashed automatically)
            django_user = DjangoUser.objects.create_user(
                username=data["username"],
                password=data["password"]
            )

            # Create app-level user
            User.objects.create(
                username=django_user.username,
                email=data.get("email", "")
            )

            logger.info(f"New user created securely: {django_user.username}")

            return Response(
                {"message": "User created securely"},
                status=status.HTTP_201_CREATED
            )

        logger.warning("User creation failed due to validation error")

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ============================
# TASKS (SECURED + FACTORY)
# ============================

class TaskListCreate(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tasks = Task.objects.all()
        serializer = TaskSerializer(tasks, many=True)

        logger.info(f"Task list accessed by user: {request.user}")

        return Response(serializer.data)

    def post(self, request):
        serializer = TaskSerializer(data=request.data)

        if serializer.is_valid():
            data = serializer.validated_data

            # ✅ CREATE TASK USING FACTORY
            task = TaskFactory.create_task(
                title=data["title"],
                description=data["description"],
                user=request.user
            )

            logger.info(f"Task created via factory (ID: {task.id})")

            return Response(
                {"message": "Task created successfully"},
                status=status.HTTP_201_CREATED
            )

        logger.warning("Task creation failed due to validation error")

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ============================
# TASK DETAIL (RBAC ENFORCED)
# ============================

class TaskDetailView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsTaskAssignee]

    def get(self, request, pk):
        try:
            task = Task.objects.get(pk=pk)
        except Task.DoesNotExist:
            logger.warning(f"Attempted access to non-existent task (ID: {pk})")

            return Response(
                {"error": "Task not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Enforce RBAC
        self.check_object_permissions(request, task)

        logger.info(
            f"Task accessed (ID: {task.id}) by user: {request.user}"
        )

        serializer = TaskSerializer(task)
        return Response(serializer.data)
