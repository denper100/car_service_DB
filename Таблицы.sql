-- 1. Workshops
CREATE TABLE workshops (
    workshop_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

-- 2. Teams  -- Перемещена выше, так как на неё есть ссылка в personnel
CREATE TABLE teams (
    team_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

-- 3. Personnel 
CREATE TABLE personnel (
    workshop_id INT NOT NULL,
    inn CHAR(12) NOT NULL,  
    team_id INT,
    PRIMARY KEY (workshop_id, inn),
    FOREIGN KEY (workshop_id) REFERENCES workshops (workshop_id) ON DELETE CASCADE,
    FOREIGN KEY (team_id) REFERENCES teams (team_id) ON DELETE SET NULL
);

-- 4. Cars
CREATE TABLE cars (
    car_id SERIAL PRIMARY KEY,
    body_number VARCHAR(50) UNIQUE NOT NULL,
    engine_number VARCHAR(50) UNIQUE NOT NULL,
    owner VARCHAR(100) NOT NULL,
    factory_number VARCHAR(50) UNIQUE NOT NULL
);

-- 5. Faults
CREATE TABLE faults (
    fault_id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    work_cost NUMERIC(10, 2) NOT NULL CHECK (work_cost >= 0)
);

-- 6. Car Repair
CREATE TABLE car_repair (
    repair_id SERIAL PRIMARY KEY,  -- Суррогатный ключ
    car_id INT NOT NULL,
    fault_id INT NOT NULL,
    admission_date DATE NOT NULL,
    completion_date DATE,
    team_id INT,
    FOREIGN KEY (car_id) REFERENCES cars (car_id) ON DELETE CASCADE,
    FOREIGN KEY (fault_id) REFERENCES faults (fault_id) ON DELETE CASCADE,
    FOREIGN KEY (team_id) REFERENCES teams (team_id) ON DELETE SET NULL,
    CHECK (completion_date IS NULL OR completion_date >= admission_date)
);

-- 7. Spare Parts
CREATE TABLE spare_parts (
    part_id SERIAL PRIMARY KEY,  -- Суррогатный ключ для уникальности
    car_id INT NOT NULL,
    fault_id INT NOT NULL,
    name VARCHAR(200) NOT NULL,
    price NUMERIC(10, 2) NOT NULL CHECK (price >= 0),
    quantity INT NOT NULL CHECK (quantity > 0),
    FOREIGN KEY (car_id) REFERENCES cars (car_id) ON DELETE CASCADE,
    FOREIGN KEY (fault_id) REFERENCES faults (fault_id) ON DELETE CASCADE
);