from backend.app.validator import validate

def test_valid_timetable():
    rooms=[{"room_id":"R1","capacity":"50","room_type":"lecture hall","special_equipment":"none"}]
    courses=[{"course_id":"C1","min_room_capacity":"20","room_type_required":"lecture hall","equipment_required":"none"}]
    faculty=[{"faculty_id":"F1","unavailable_slots":""}]
    row={"course_id":"C1","faculty_id":"F1","section_id":"S1","room_id":"R1","day":"Mon","start_slot":1,"duration":1}
    assert validate([row],courses,rooms,faculty)==[]
def test_room_clash():
    rows=[{"course_id":"a","faculty_id":"f1","section_id":"s1","room_id":"r","day":"Tue","start_slot":2,"duration":1},{"course_id":"b","faculty_id":"f2","section_id":"s2","room_id":"r","day":"Tue","start_slot":2,"duration":1}]
    assert any("Room r" in x for x in validate(rows))
def test_wrong_equipment():
    assert validate([{"course_id":"c","faculty_id":"f","section_id":"s","room_id":"r","day":"Mon","start_slot":1}], [{"course_id":"c","min_room_capacity":1,"room_type_required":"lab","equipment_required":"network lab"}], [{"room_id":"r","capacity":2,"room_type":"lab","special_equipment":"none"}], [{"faculty_id":"f"}])
