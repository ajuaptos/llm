# Local LLM Web Application

This project is a web application that allows users to submit search queries and interact with the LiteLLM API. It is designed to provide a user-friendly interface for leveraging the capabilities of a local Large Language Model (LLM).

## Project Structure

- **public/index.html**: The main HTML page containing the search form and results display.
- **public/manifest.json**: Metadata for the web application, useful for Progressive Web Apps (PWAs).
- **src/js/app.js**: Main JavaScript file that handles form submissions and updates the DOM with results.
- **src/js/lite_llm_api.js**: Contains functions for making API calls to the LiteLLM service.
- **src/css/styles.css**: Styles for the web application, defining layout, colors, and fonts.
- **.env.example**: Template for environment variables needed for the application.
- **package.json**: Configuration file for npm, listing dependencies and scripts.
- **Dockerfile**: Instructions for building a Docker image for the web application.

## Setup Instructions

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd local-llm-web
   ```

2. **Create Environment Variables**
   Copy the `.env.example` to `.env` and fill in the required values.

3. **Install Dependencies**
   Run the following command to install the necessary dependencies:
   ```bash
   npm install
   ```

4. **Build and Start the Application**
   Use the following command to build and start the application:
   ```bash
   npm start
   ```

5. **Access the Application**
   Open your web browser and navigate to [http://localhost:3000](http://localhost:3000) to access the application.

## Usage

- Enter your search query in the provided form and submit it to interact with the LiteLLM API.
- View the results displayed on the page.

## Contributing

Contributions are welcome! Please submit a pull request or open an issue for any enhancements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.