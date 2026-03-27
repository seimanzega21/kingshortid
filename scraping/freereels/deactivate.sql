UPDATE dramas SET is_active = false WHERE tag_list::text LIKE '%Dubbing%';
UPDATE episodes SET is_active = false WHERE drama_id IN (SELECT id FROM dramas WHERE tag_list::text LIKE '%Dubbing%');
SELECT COUNT(*) as deactivated_dramas FROM dramas WHERE tag_list::text LIKE '%Dubbing%' AND is_active = false;
