import pytest
from classroom.models import Classroom
from classroom.serializers import ClassroomDetailSerializer, ClassroomListSerializer
from core.models import School


@pytest.mark.django_db
def test_classroom_list_serializer():
    """Test classroom list serializer contract."""
    school = School.objects.first()
    if not school:
        pytest.skip("No school in database")
    
    classrooms = Classroom.objects.filter(school=school)
    list_serializer = ClassroomListSerializer(classrooms, many=True)
    list_data = list_serializer.data
    
    assert isinstance(list_data, list)
    if list_data:
        assert "id" in list_data[0]
        assert "name" in list_data[0]
        assert "homeroom_teacher_name" in list_data[0]


@pytest.mark.django_db
def test_classroom_detail_serializer():
    """Test classroom detail serializer contract."""
    school = School.objects.first()
    if not school:
        pytest.skip("No school in database")
    
    classroom = Classroom.objects.filter(school=school).first()
    if not classroom:
        pytest.skip("No classroom in database")
    
    detail_serializer = ClassroomDetailSerializer(classroom)
    detail_data = detail_serializer.data
    
    # Verify contract
    assert detail_data["id"]
    assert detail_data["name"]
    assert detail_data["room"]
    assert "students" in detail_data
    assert "announcements" in detail_data
    assert "assignments" in detail_data
    assert "seating_chart" in detail_data
    assert isinstance(detail_data["students"], list)
    assert isinstance(detail_data["announcements"], list)
    assert isinstance(detail_data["assignments"], list)
