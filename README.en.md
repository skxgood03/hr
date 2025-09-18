

# Human Resources Payroll Management System (HRPMS)

A modern human resources payroll management system based on Django, focusing on employee information management, salary calculation, attendance management and other core functions.

This project is a Django-based HR Payroll Management System that focuses on core functions of human resources management and payroll management for enterprises. The system includes functional modules such as department management, employee information management, position management, salary management, and attendance management. The project implements API-based CRUD (Create, Read, Update, Delete) operations using Django REST framework, making it suitable for building a frontend-backend decoupled HR payroll management system.

## Functional Modules

### Department Management (department)
- Add, delete, search, and modify department information
- Display list of departments
- View department details

### Employee Management (personal)
- Add, delete, search, and modify employee information
- Display list of employees
- Retrieve employee information by department
- Calculate employee age

### Recruitment Management (recruit)
- Add, delete, search, and modify recruitment information
- Display list of recruitment entries
- View recruitment details

### Salary Management (salary_management)
- Add, delete, search, and modify salary information
- Display salary list
- View salary details
- Salary calculation (including bonus amounts)

### Position Management (station)
- Add, delete, search, and modify position information
- Display list of positions
- Retrieve position information by department

### Training Management (train)
- Add, delete, search, and modify training information
- Display training list
- View training details

### Rewards Management (rewards)
- Add, delete, search, and modify reward information
- Display list of rewards
- View reward details

### User Authentication (hr)
- User login
- User logout
- Role-based access control

### Return Value Wrappers
- `ResultVo`: Used to encapsulate operation results (success/failure) and data.
- `ResultPageVo`: Used to encapsulate paginated query results.

## Technology Stack
- Python
- Django
- Django REST framework

## Installation and Execution
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Migrate the database:
   ```bash
   python manage.py migrate
   ```
3. Start the development server:
   ```bash
   python manage.py runserver
   ```

## Usage Instructions
- All modules provide API-based interfaces that support operations via POST, GET, PUT, and DELETE methods.
- API endpoints are defined in the `urls.py` file of each module.
- Data models are defined in the `models.py` file of each module.
- Serializers are defined in the `serializers.py` file of each module.

## Contribution
Feel free to submit issues and pull requests to improve this project.

## License
This project uses the MIT License. Please refer to the license file for details.