db.getSiblingDB('jiriaf').createUser({
  user: 'jiriaf',
  pwd: 'jiriaf',
  roles: [{role: 'readWrite', db: 'jiriaf'}]
}); 