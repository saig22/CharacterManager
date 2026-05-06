CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL
);

INSERT INTO users (username, email) VALUES
('admin', 'admin@example.com');

CREATE TABLE IF NOT EXISTS worlds (
    world_name VARCHAR(255) PRIMARY KEY,
    world_description VARCHAR(255) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS character_type (
    type_name VARCHAR(255) PRIMARY KEY,
    type_description VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS characters (
    character_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    character_name VARCHAR(255) UNIQUE NOT NULL,
    armor VARCHAR(255) NOT NULL,
    weapon VARCHAR(255) NOT NULL,
    inventory VARCHAR(255) NOT NULL,
    age INT NOT NULL,
    attributes VARCHAR(255) NOT NULL,
    world_name VARCHAR(255) NOT NULL,
    type_name VARCHAR(255) NOT NULL,
    FOREIGN KEY (world_name) REFERENCES worlds(world_name) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (type_name) REFERENCES character_type(type_name) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS character_attributes (
    character_id INT PRIMARY KEY,
    attribute varchar(255) NOT NULL,
    FOREIGN KEY (character_id) REFERENCES characters(character_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS world_characters (
    world_name VARCHAR(255) NOT NULL,
    character_type VARCHAR(255) NOT NULL,
    PRIMARY KEY (world_name, character_type),
    FOREIGN KEY (world_name) REFERENCES worlds(world_name) ON DELETE CASCADE,
    FOREIGN KEY (character_type) REFERENCES character_type(type_name) ON DELETE CASCADE
);

INSERT INTO worlds (world_name, world_description) VALUES
('Fantasy Realm', 'A magical world filled with mythical creatures and epic adventures.'),
('Sci-Fi Universe', 'A futuristic world with advanced technology and space exploration.'),
('Post-Apocalyptic Wasteland', 'A desolate world ravaged by disaster, where survival is key.');

INSERT INTO character_type (type_name, type_description) VALUES
('Warrior', 'A strong and brave fighter skilled in melee combat.'),
('Mage', 'A master of magical arts, capable of casting powerful spells.'),
('Rogue', 'A stealthy and agile character, adept at sneaking and thievery.');

INSERT INTO world_characters (world_name, character_type) VALUES
('Fantasy Realm', 'Warrior'),
('Sci-Fi Universe', 'Mage'),
('Post-Apocalyptic Wasteland', 'Rogue');

delimiter $$
CREATE TRIGGER before_insert_character
BEFORE INSERT ON characters
FOR EACH ROW
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM world_characters
        WHERE world_name = NEW.world_name
          AND character_type = NEW.type_name
    ) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Character type not allowed in world';
    END IF;
END$$

CREATE TRIGGER before_update_character
BEFORE UPDATE ON characters
FOR EACH ROW
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM world_characters
        WHERE world_name = NEW.world_name
          AND character_type = NEW.type_name
    ) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Character type not allowed in world';
    END IF;
END$$
delimiter ;

INSERT INTO characters (user_id, world_name, type_name, character_name, armor, weapon, inventory, age, attributes) VALUES
(1, 'Fantasy Realm', 'Warrior', 'Aragorn', 'Plate Armor', 'Longsword', 'Health Potion, Gold Coins', 87, 'Strength: 90, Dexterity: 75, Intelligence: 60');