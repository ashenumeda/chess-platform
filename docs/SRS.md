# Software Requirements Specification (SRS)
## Online Chess Platform

---

## 1. Introduction

### 1.1 Purpose
This document specifies the functional and non-functional requirements
for an Online Chess Platform. The system allows users to register, log in,
invite other users, and play chess games online.

### 1.2 Scope
The Online Chess Platform will provide:
- User authentication (Email/Password and Google OAuth)
- Account linking across authentication methods
- Game invitations via shareable links
- Online chess gameplay
- Legal move validation and visualization
- Match history tracking
- Basic user profile management

This system is developed as a personal project to demonstrate
software engineering and full-stack development skills.

### 1.3 Definitions, Acronyms, and Abbreviations
- OAuth: Open Authorization
- UI: User Interface
- UML: Unified Modeling Language
- API: Application Programming Interface

---

## 2. Overall Description

### 2.1 Product Perspective
The system is a web-based application consisting of:
- Frontend client (browser-based UI)
- Backend server (authentication, game logic)
- Database (users, invitations, games)

### 2.2 Product Functions
- User registration and login
- Game invitation creation and acceptance
- Online chess gameplay
- Chess rule enforcement
- Display of legal moves
- Game result storage

### 2.3 Tech Stack
- **Frontend:** React.js (Vite)
- **Backend:** Python with FastAPI
- **Database:** PostgreSQL
- **Real-Time Communication:** WebSockets
- **Authentication:** Google OAuth + Email/Password
- **Version Control:** Git/GitHub
- **Diagram Tools:** Lucidchart for UML diagrams

### 2.4 User Classes and Characteristics
- **Registered User:** Can invite others, accept invitations, and play games
- **Guest User:** Cannot play games or create invitations

### 2.5 Operating Environment
- Modern web browsers (Chrome, Firefox, Edge)
- Backend server on Linux or Windows
- Internet connection required

### 2.6 Design and Implementation Constraints
- Must follow standard chess rules
- OAuth depends on third-party providers
- Secure handling of authentication and invitations

### 2.7 Assumptions and Dependencies
- Users have a stable internet connection
- Google OAuth service availability
- Chess rules follow FIDE standards

---

## 3. System Features (Functional Requirements)

### 3.1 User Authentication

**FR-1:** The system shall allow users to register using an email address
and password.

**FR-2:** The system shall allow users to log in using an email address
and password.

**FR-3:** The system shall allow users to log in using Google OAuth.

**FR-3A:** The system shall securely store user passwords using hashing
techniques.

**FR-4:** The system shall uniquely identify users using their email
address.

**FR-4A:** If a user registers using email and password and later logs in
using Google OAuth with the same email address, the system shall recognize
both logins as the same user account.

**FR-4B:** The system shall link OAuth-based authentication to an existing
user account when the email address matches.

---

### 3.2 User Profile Management

**FR-5:** The system shall allow users to view their profile information.

**FR-6:** The system shall display basic statistics such as total games
played and games won.

---

### 3.3 Game Invitation System

**FR-7:** The system shall allow an authenticated user to create a game
invitation.

**FR-8:** The system shall generate a unique, shareable invitation link
for each invitation.

**FR-9:** The system shall allow another authenticated user to accept a
game invitation using the invitation link.

**FR-10:** The system shall create a new chess game only after an
invitation is accepted.

**FR-11:** The system shall prevent an invitation from being used more
than once.

---

### 3.4 Gameplay

**FR-12:** The system shall allow two authenticated users to play a game
of chess after invitation acceptance.

**FR-13:** The system shall enforce standard chess rules.

**FR-14:** The system shall validate each move before applying it to the
game state.

**FR-14A:** The system shall display all legal moves for a selected chess
piece before the player makes a move.

**FR-15:** The system shall detect check, checkmate, and draw conditions.

**FR-16:** The system shall declare a winner at the end of a game.

---

### 3.5 Match History

**FR-17:** The system shall store completed games.

**FR-18:** The system shall allow users to view their past match history.

---

## 4. Non-Functional Requirements

### 4.1 Performance
**NFR-1:** The system shall respond to user actions within 200 ms under
normal conditions.

### 4.2 Security
**NFR-2:** The system shall encrypt sensitive user data.

**NFR-3:** The system shall ensure invitation links are hard to guess and
secure.

### 4.3 Reliability
**NFR-4:** The system shall maintain consistent game state during gameplay.

### 4.4 Usability
**NFR-5:** The system shall provide an intuitive user interface.

**NFR-6:** The system shall clearly highlight legal chess moves.

### 4.5 Scalability
**NFR-7:** The system shall support multiple concurrent games.

---

## 5. External Interface Requirements

### 5.1 User Interfaces
- Login and registration pages
- Invitation creation and sharing interface
- Chessboard with move highlights
- Match history page

### 5.2 Software Interfaces
- Google OAuth API
- Database management system

---

## 6. Assumptions and Dependencies
- Users have internet access
- OAuth provider availability
- Chess rules comply with FIDE standards

---

## 7. Future Enhancements
- Spectator mode
- Real-time chat
- Chess AI opponent
- Tournament support
- Facebook OAuth support
