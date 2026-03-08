-- Upgrade existing user to admin and update credentials
UPDATE users SET name='Seiman Zega', role='admin', password='$2b$10$KQasr8cgau01MfGA5BbHBOdy3uFH4yySvtX49ZMWZGSkp.xdTQc9y' WHERE email='dhikacreative25@gmail.com';
-- Keep old admin but remove admin role (downgrade to user)
UPDATE users SET role='user' WHERE email='admin@kingshort.com';
