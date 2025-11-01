/**
 * ============================================================================
 * WEBSOCKET CONNECTION SETUP / WEBSOCKET-VERBINDUNGSAUFBAU
 * ============================================================================
 * 
 * This section establishes a WebSocket connection to enable real-time,
 * bidirectional communication between the client and server.
 * 
 * WebSocket ist ein Kommunikationsprotokoll, das eine Vollduplex-
 * Kommunikationsverbindung über eine einzelne TCP-Verbindung bereitstellt.
 * 
 * Technical Reference / Technische Referenz:
 * - WebSocket API: https://developer.mozilla.org/en-US/docs/Web/API/WebSocket
 * - RFC 6455 (WebSocket Protocol): https://tools.ietf.org/html/rfc6455
 * - W3C WebSocket API Specification: https://www.w3.org/TR/websockets/
 */

/**
 * Create a new WebSocket connection / Erstellt eine neue WebSocket-Verbindung
 * 
 * @constant {WebSocket} ws - The WebSocket instance for real-time communication
 * 
 * Implementation Details / Implementierungsdetails:
 * - Uses template literals to dynamically construct the WebSocket URL
 * - window.location.hostname: Gets the current page's hostname (e.g., "localhost")
 *   Reference: https://developer.mozilla.org/en-US/docs/Web/API/Location/hostname
 * - Port 3000: The server-side WebSocket endpoint listening port
 * - ws:// protocol: Non-encrypted WebSocket (use wss:// for production with SSL/TLS)
 * 
 * Example URL construction:
 * If hostname is "localhost" → WebSocket URL becomes "ws://localhost:3000"
 * If hostname is "192.168.1.100" → WebSocket URL becomes "ws://192.168.1.100:3000"
 * 
 * Security Note / Sicherheitshinweis:
 * In production environments, use wss:// (WebSocket Secure) instead of ws://
 * to encrypt communication. Reference: https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API/Writing_WebSocket_servers
 */
const ws = new WebSocket(`ws://${window.location.hostname}:3000`);

/**
 * ============================================================================
 * DOM ELEMENT REFERENCES / DOM-ELEMENTREFERENZEN
 * ============================================================================
 * 
 * This section caches references to HTML DOM elements for efficient access
 * throughout the application lifecycle. Caching prevents repeated DOM queries.
 * 
 * Diese Sektion speichert Referenzen auf HTML-DOM-Elemente für effizienten
 * Zugriff während des gesamten Anwendungslebenszyklus.
 * 
 * Technical Reference / Technische Referenz:
 * - document.getElementById(): https://developer.mozilla.org/en-US/docs/Web/API/Document/getElementById
 * - DOM Performance Best Practices: https://developer.mozilla.org/en-US/docs/Web/API/Document_Object_Model/Introduction
 * 
 * Performance Note / Leistungshinweis:
 * Caching DOM references improves performance by avoiding repeated DOM traversal.
 * Each getElementById() call traverses the DOM tree, so caching is more efficient.
 */

/**
 * Connection status display element / Verbindungsstatus-Anzeigeelement
 * 
 * @constant {HTMLElement} connectionStatus - Shows the WebSocket connection state
 * 
 * Purpose / Zweck:
 * Displays "Connected" or "Disconnected" status to inform users about
 * the real-time connection state with the server.
 * 
 * HTML Reference: <div id="connection-status" class="connection-badge offline">
 */
const connectionStatus = document.getElementById('connection-status');

/**
 * Nitrogen (N) value display element / Stickstoff (N) Wertanzeigeelement
 * 
 * @constant {HTMLElement} nValue - Displays current nitrogen level in PPM
 * 
 * Purpose / Zweck:
 * Shows the current nitrogen concentration in the hydroponic solution.
 * PPM (Parts Per Million) is a standard unit for nutrient concentration.
 * 
 * Reference: Hydroponic NPK ratios - https://en.wikipedia.org/wiki/Hydroponics
 * HTML Reference: <div class="nutrient-value" id="n-value">
 */
const nValue = document.getElementById('n-value');

/**
 * Phosphorus (P) value display element / Phosphor (P) Wertanzeigeelement
 * 
 * @constant {HTMLElement} pValue - Displays current phosphorus level in PPM
 * 
 * Purpose / Zweck:
 * Shows the current phosphorus concentration in the hydroponic solution.
 * Phosphorus is essential for root development and energy transfer.
 * 
 * HTML Reference: <div class="nutrient-value" id="p-value">
 */
const pValue = document.getElementById('p-value');

/**
 * Potassium (K) value display element / Kalium (K) Wertanzeigeelement
 * 
 * @constant {HTMLElement} kValue - Displays current potassium level in PPM
 * 
 * Purpose / Zweck:
 * Shows the current potassium concentration in the hydroponic solution.
 * Potassium is vital for protein synthesis and disease resistance.
 * 
 * HTML Reference: <div class="nutrient-value" id="k-value">
 */
const kValue = document.getElementById('k-value');

/**
 * Nitrogen control slider / Stickstoff-Kontrollschieberegler
 * 
 * @constant {HTMLInputElement} nSlider - Range input for nitrogen adjustment
 * 
 * Purpose / Zweck:
 * Allows users to set the target nitrogen level (0-200 PPM range).
 * Input type="range" provides a native slider UI component.
 * 
 * Reference: HTML Range Input - https://developer.mozilla.org/en-US/docs/Web/HTML/Element/input/range
 * HTML Reference: <input type="range" min="0" max="200" id="n-slider">
 */
const nSlider = document.getElementById('n-slider');

/**
 * Phosphorus control slider / Phosphor-Kontrollschieberegler
 * 
 * @constant {HTMLInputElement} pSlider - Range input for phosphorus adjustment
 * 
 * Purpose / Zweck:
 * Allows users to set the target phosphorus level (0-150 PPM range).
 * 
 * HTML Reference: <input type="range" min="0" max="150" id="p-slider">
 */
const pSlider = document.getElementById('p-slider');

/**
 * Potassium control slider / Kalium-Kontrollschieberegler
 * 
 * @constant {HTMLInputElement} kSlider - Range input for potassium adjustment
 * 
 * Purpose / Zweck:
 * Allows users to set the target potassium level (0-250 PPM range).
 * 
 * HTML Reference: <input type="range" min="0" max="250" id="k-slider">
 */
const kSlider = document.getElementById('k-slider');

/**
 * Light control toggle switch / Licht-Umschaltschalter
 * 
 * @constant {HTMLInputElement} lightToggle - Checkbox input for light control
 * 
 * Purpose / Zweck:
 * Toggle switch to control the grow lights in the hydroponic system.
 * Implemented as a styled checkbox for ON/OFF control.
 * 
 * Reference: Checkbox Input - https://developer.mozilla.org/en-US/docs/Web/HTML/Element/input/checkbox
 * HTML Reference: <input type="checkbox" id="light-toggle">
 */
const lightToggle = document.getElementById('light-toggle');

/**
 * Light status display / Lichtstatusanzeige
 * 
 * @constant {HTMLElement} lightStatus - Shows current light state (ON/OFF)
 * 
 * Purpose / Zweck:
 * Displays the current state of the grow lights as text ("ON" or "OFF").
 * 
 * HTML Reference: <div id="light-status" class="status-text">
 */
const lightStatus = document.getElementById('light-status');

/**
 * ============================================================================
 * WEBSOCKET CONNECTION EVENT HANDLERS / WEBSOCKET-VERBINDUNGS-EVENT-HANDLER
 * ============================================================================
 * 
 * This section defines event handlers for WebSocket lifecycle events.
 * WebSocket has four main events: onopen, onmessage, onerror, and onclose.
 * 
 * Diese Sektion definiert Event-Handler für WebSocket-Lebenszyklus-Ereignisse.
 * 
 * Technical Reference / Technische Referenz:
 * - WebSocket Events: https://developer.mozilla.org/en-US/docs/Web/API/WebSocket#events
 * - WebSocket readyState: https://developer.mozilla.org/en-US/docs/Web/API/WebSocket/readyState
 */

/**
 * WebSocket 'open' event handler / WebSocket 'open' Event-Handler
 * 
 * @event onopen
 * @description Triggered when the WebSocket connection is successfully established
 * 
 * Event Flow / Ereignisablauf:
 * 1. WebSocket handshake completes successfully
 * 2. Connection state changes to OPEN (readyState = 1)
 * 3. This handler is invoked automatically
 * 
 * Implementation / Implementierung:
 * Uses arrow function syntax for concise event handler definition.
 * Arrow functions: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Functions/Arrow_functions
 * 
 * @callback
 * @returns {void}
 */
ws.onopen = () => {
    /**
     * Update the connection status text / Aktualisiert den Verbindungsstatustext
     * 
     * Sets the textContent property to display "Connected" to the user.
     * textContent is preferred over innerHTML for security (no HTML parsing).
     * 
     * Reference: textContent vs innerHTML
     * https://developer.mozilla.org/en-US/docs/Web/API/Node/textContent
     * 
     * Security Note / Sicherheitshinweis:
     * Using textContent prevents XSS (Cross-Site Scripting) attacks by treating
     * content as plain text rather than parsing it as HTML.
     */
    connectionStatus.textContent = "Connected";
    
    /**
     * Update the CSS class for visual styling / Aktualisiert die CSS-Klasse für visuelle Gestaltung
     * 
     * classList.replace() swaps one CSS class for another atomically.
     * - Removes the 'offline' class (red/disconnected styling)
     * - Adds the 'online' class (green/connected styling)
     * 
     * Method: Element.classList.replace(oldClass, newClass)
     * Reference: https://developer.mozilla.org/en-US/docs/Web/API/DOMTokenList/replace
     * 
     * Browser Compatibility / Browser-Kompatibilität:
     * Supported in all modern browsers (Chrome 61+, Firefox 49+, Safari 10.1+)
     * Fallback: Use classList.remove() and classList.add() for older browsers
     */
    connectionStatus.classList.replace('offline', 'online');
};

/**
 * WebSocket 'close' event handler / WebSocket 'close' Event-Handler
 * 
 * @event onclose
 * @description Triggered when the WebSocket connection is closed
 * 
 * Trigger Conditions / Auslösebedingungen:
 * - Server closes the connection
 * - Network failure or timeout
 * - Client explicitly calls ws.close()
 * - Browser/tab is closed
 * 
 * Event Flow / Ereignisablauf:
 * 1. Connection is terminated (readyState changes to CLOSED = 3)
 * 2. This handler is invoked automatically
 * 3. UI is updated to reflect disconnected state
 * 
 * Reference: WebSocket close event
 * https://developer.mozilla.org/en-US/docs/Web/API/WebSocket/close_event
 * 
 * @callback
 * @returns {void}
 */
ws.onclose = () => {
    /**
     * Update the connection status text / Aktualisiert den Verbindungsstatustext
     * 
     * Sets the textContent property to display "Disconnected" to the user.
     */
    connectionStatus.textContent = "Disconnected";
    
    /**
     * Update the CSS class for visual styling / Aktualisiert die CSS-Klasse für visuelle Gestaltung
     * 
     * classList.replace() swaps CSS classes:
     * - Removes the 'online' class (green/connected styling)
     * - Adds the 'offline' class (red/disconnected styling)
     * 
     * User Experience Note / Benutzererfahrungshinweis:
     * Visual feedback is crucial for real-time applications to inform users
     * about connectivity issues immediately.
     */
    connectionStatus.classList.replace('online', 'offline');
};

/**
 * ============================================================================
 * WEBSOCKET MESSAGE HANDLER / WEBSOCKET-NACHRICHTEN-HANDLER
 * ============================================================================
 * 
 * This section handles incoming messages from the WebSocket server.
 * Messages contain real-time sensor data from the hydroponic system's IoT devices.
 * 
 * Diese Sektion behandelt eingehende Nachrichten vom WebSocket-Server.
 * 
 * Technical Reference / Technische Referenz:
 * - WebSocket message event: https://developer.mozilla.org/en-US/docs/Web/API/WebSocket/message_event
 * - JSON.parse(): https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/JSON/parse
 * 
 * Data Flow / Datenfluss:
 * IoT Device → Server (via WebSocket/HTTP) → This Client (via WebSocket) → UI Update
 */

/**
 * WebSocket 'message' event handler / WebSocket 'message' Event-Handler
 * 
 * @event onmessage
 * @description Processes incoming messages containing sensor data and system status
 * 
 * @callback
 * @param {MessageEvent} event - The message event object from WebSocket
 * @param {string} event.data - The raw message data (JSON string format)
 * 
 * Event Properties / Ereigniseigenschaften:
 * - event.data: Contains the actual message payload as a string
 * - event.origin: The origin of the WebSocket connection
 * - event.lastEventId: The last event ID (for Server-Sent Events)
 * 
 * Reference: MessageEvent interface
 * https://developer.mozilla.org/en-US/docs/Web/API/MessageEvent
 * 
 * @returns {void}
 */
ws.onmessage = (event) => {
    /**
     * Parse the JSON message / Analysiert die JSON-Nachricht
     * 
     * JSON.parse() converts a JSON-formatted string into a JavaScript object.
     * 
     * Expected Message Format / Erwartetes Nachrichtenformat:
     * {
     *   "type": "sensorData",
     *   "temperature": 22.5,
     *   "ph": 6.2,
     *   "waterLevel": 85,
     *   "nitrogen": 120,
     *   "phosphorus": 45,
     *   "potassium": 180,
     *   "lightsOn": true
     * }
     * 
     * Error Handling Note / Fehlerbehandlungshinweis:
     * In production, wrap this in try-catch to handle malformed JSON gracefully.
     * Example: try { const data = JSON.parse(event.data); } catch(e) { console.error(e); }
     * 
     * Reference: JSON format specification
     * https://www.json.org/json-en.html
     * 
     * @constant {Object} data - Parsed JavaScript object containing sensor readings
     */
    const data = JSON.parse(event.data);
    
    /**
     * Check message type / Überprüft den Nachrichtentyp
     * 
     * Message Type Discrimination / Nachrichten-Typ-Unterscheidung:
     * Different message types allow for extensible protocol design.
     * Current types: 'sensorData', future types could include 'alert', 'command', etc.
     * 
     * Conditional Logic / Bedingte Logik:
     * Uses strict equality (===) for type checking to avoid type coercion issues.
     * Reference: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Strict_equality
     * 
     * Design Pattern / Entwurfsmuster:
     * This implements a simple message type router pattern for handling
     * different message types from the server.
     */
    if (data.type === 'sensorData') {
        /**
         * ====================================================================
         * UPDATE ENVIRONMENTAL SENSOR READINGS / AKTUALISIERT UMWELTSENSORMESSUNGEN
         * ====================================================================
         */
        
        /**
         * Update temperature display / Aktualisiert Temperaturanzeige
         * 
         * Temperature units: Celsius (°C)
         * Typical range for hydroponics: 18-24°C (64-75°F)
         * 
         * Template Literal / Template-Literal:
         * Uses backticks (`) for string interpolation with ${expression} syntax.
         * Reference: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Template_literals
         * 
         * Unicode Character: °C (degree Celsius symbol)
         * Reference: https://unicode-table.com/en/00B0/
         */
        document.getElementById('temperature').textContent = `${data.temperature}°C`;
        
        /**
         * Update pH level display / Aktualisiert pH-Wert-Anzeige
         * 
         * pH Scale: 0-14, where 7 is neutral
         * Optimal pH for hydroponics: 5.5-6.5 (slightly acidic)
         * 
         * Why pH matters / Warum pH wichtig ist:
         * pH affects nutrient availability. Outside the optimal range, plants
         * cannot absorb nutrients effectively, even if present in solution.
         * 
         * Reference: Hydroponic pH management
         * https://en.wikipedia.org/wiki/Hydroponics#Nutrients_and_pH
         */
        document.getElementById('ph-level').textContent = data.ph;
        
        /**
         * Update water level display / Aktualisiert Wasserpegel-Anzeige
         * 
         * Unit: Percentage (0-100%)
         * 
         * Purpose / Zweck:
         * Monitors reservoir water level to prevent pump damage and ensure
         * adequate solution for plant roots. Low levels trigger refill alerts.
         */
        document.getElementById('water-level').textContent = `${data.waterLevel}%`;
        
        /**
         * ====================================================================
         * UPDATE NPK NUTRIENT LEVELS / AKTUALISIERT NPK-NÄHRSTOFFWERTE
         * ====================================================================
         * 
         * NPK refers to the three primary macronutrients:
         * - N (Nitrogen): Promotes leafy growth and green color
         * - P (Phosphorus): Supports root development and flowering
         * - K (Potassium): Enhances overall plant health and disease resistance
         * 
         * Measurement Unit: PPM (Parts Per Million)
         * Reference: https://en.wikipedia.org/wiki/Parts-per_notation
         */
        
        /**
         * Update nitrogen (N) level display / Aktualisiert Stickstoff (N) Pegelanzeige
         * 
         * Typical N range for hydroponics: 100-200 PPM
         * 
         * Plant Science / Pflanzenwissenschaft:
         * Nitrogen is essential for chlorophyll production and photosynthesis.
         * Deficiency symptoms: yellowing leaves (chlorosis), stunted growth.
         */
        nValue.textContent = `${data.nitrogen} ppm`;
        
        /**
         * Update phosphorus (P) level display / Aktualisiert Phosphor (P) Pegelanzeige
         * 
         * Typical P range for hydroponics: 30-50 PPM
         * 
         * Plant Science / Pflanzenwissenschaft:
         * Phosphorus is crucial for energy transfer (ATP) and root development.
         * Deficiency symptoms: dark green or purple leaves, weak roots.
         */
        pValue.textContent = `${data.phosphorus} ppm`;
        
        /**
         * Update potassium (K) level display / Aktualisiert Kalium (K) Pegelanzeige
         * 
         * Typical K range for hydroponics: 150-250 PPM
         * 
         * Plant Science / Pflanzenwissenschaft:
         * Potassium regulates water uptake and enzyme activation.
         * Deficiency symptoms: brown leaf edges, weak stems.
         */
        kValue.textContent = `${data.potassium} ppm`;
        
        /**
         * ====================================================================
         * UPDATE LIGHT CONTROL STATUS / AKTUALISIERT LICHTSTEUERUNGSSTATUS
         * ====================================================================
         */
        
        /**
         * Update light toggle checkbox state / Aktualisiert Lichtschalter-Checkbox-Zustand
         * 
         * Property: checked (boolean)
         * - true: Checkbox is checked (lights ON)
         * - false: Checkbox is unchecked (lights OFF)
         * 
         * Purpose / Zweck:
         * Synchronizes the UI toggle switch with the actual hardware state.
         * This ensures the UI reflects reality when controlled from other sources
         * (e.g., automated schedules, physical switches, or other clients).
         * 
         * Reference: HTMLInputElement.checked
         * https://developer.mozilla.org/en-US/docs/Web/API/HTMLInputElement
         */
        lightToggle.checked = data.lightsOn;
        
        /**
         * Update light status text / Aktualisiert Lichtstatustext
         * 
         * Ternary Operator / Ternärer Operator:
         * Syntax: condition ? expressionIfTrue : expressionIfFalse
         * 
         * Logic / Logik:
         * If data.lightsOn is true → display "ON"
         * If data.lightsOn is false → display "OFF"
         * 
         * Reference: Conditional (ternary) operator
         * https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Conditional_Operator
         * 
         * User Experience / Benutzererfahrung:
         * Provides clear textual feedback alongside the toggle switch for
         * accessibility and clarity.
         */
        lightStatus.textContent = data.lightsOn ? "ON" : "OFF";
    }
};

/**
 * ============================================================================
 * NUTRIENT CONTROL EVENT LISTENERS / NÄHRSTOFFSTEUERUNGS-EVENT-LISTENER
 * ============================================================================
 * 
 * This section implements real-time nutrient level control through slider inputs.
 * Each slider sends commands to adjust the target concentration of a specific nutrient.
 * 
 * Diese Sektion implementiert Echtzeit-Nährstoffpegelsteuerung durch Schieberegler-Eingaben.
 * 
 * Technical Reference / Technische Referenz:
 * - addEventListener(): https://developer.mozilla.org/en-US/docs/Web/API/EventTarget/addEventListener
 * - Input event: https://developer.mozilla.org/en-US/docs/Web/API/HTMLElement/input_event
 * - WebSocket.send(): https://developer.mozilla.org/en-US/docs/Web/API/WebSocket/send
 * 
 * Design Pattern / Entwurfsmuster:
 * Event-Driven Architecture - UI changes trigger immediate server notifications
 * for real-time system response.
 */

/**
 * Nitrogen (N) slider input event listener / Stickstoff (N) Schieberegler Input Event Listener
 * 
 * @event input
 * @description Triggers continuously as the user drags the nitrogen slider
 * 
 * Event Type: 'input' / Ereignistyp: 'input'
 * - Fires every time the slider value changes (during drag)
 * - More responsive than 'change' event (which fires only on release)
 * 
 * Alternative Event / Alternatives Ereignis:
 * - 'change': Fires only when user finishes adjusting (mouseup)
 * - 'input': Fires during adjustment (real-time)
 * 
 * Choice Rationale / Wahlbegründung:
 * Using 'input' provides immediate feedback and real-time control,
 * enhancing user experience in precision agriculture applications.
 * 
 * Reference: Input vs Change events
 * https://developer.mozilla.org/en-US/docs/Web/API/HTMLElement/input_event
 * 
 * @callback
 * @param {Event} e - The input event object
 * @param {HTMLInputElement} e.target - The slider element that triggered the event
 * @param {string} e.target.value - The current slider value (0-200)
 * @returns {void}
 */
nSlider.addEventListener('input', (e) => {
    /**
     * Send nutrient control command via WebSocket / Sendet Nährstoffsteuerungsbefehl über WebSocket
     * 
     * WebSocket.send() transmits data to the server.
     * - Only works when WebSocket state is OPEN (readyState === 1)
     * - Accepts string, ArrayBuffer, or Blob data
     * 
     * Message Structure / Nachrichtenstruktur:
     * {
     *   "type": "nutrientControl",      // Command type identifier
     *   "nutrient": "nitrogen",          // Which nutrient to adjust
     *   "value": "150"                   // Target value from slider
     * }
     * 
     * JSON.stringify() converts JavaScript object to JSON string for transmission.
     * Reference: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/JSON/stringify
     * 
     * Server-Side Handling / Serverseitige Verarbeitung:
     * The server receives this message and:
     * 1. Validates the command
     * 2. Sends control signals to IoT hardware
     * 3. Updates dosing pumps or valves accordingly
     * 
     * Safety Note / Sicherheitshinweis:
     * In production, implement rate limiting to prevent command flooding
     * and add validation to ensure values are within safe operating ranges.
     */
    ws.send(JSON.stringify({
        type: 'nutrientControl',
        nutrient: 'nitrogen',
        value: e.target.value
    }));
});

/**
 * Phosphorus (P) slider input event listener / Phosphor (P) Schieberegler Input Event Listener
 * 
 * @event input
 * @description Triggers continuously as the user drags the phosphorus slider
 * 
 * Functionality / Funktionalität:
 * Identical to nitrogen slider but controls phosphorus dosing system.
 * 
 * Slider Range / Schiebereglerbereich:
 * 0-150 PPM (defined in HTML: min="0" max="150")
 * 
 * @callback
 * @param {Event} e - The input event object
 * @param {HTMLInputElement} e.target - The slider element
 * @param {string} e.target.value - Current slider value (0-150)
 * @returns {void}
 */
pSlider.addEventListener('input', (e) => {
    /**
     * Send phosphorus control command / Sendet Phosphor-Steuerungsbefehl
     * 
     * Command structure matches nitrogen control for consistency.
     * Different nutrient identifier allows server to route to correct hardware.
     */
    ws.send(JSON.stringify({
        type: 'nutrientControl',
        nutrient: 'phosphorus',
        value: e.target.value
    }));
});

/**
 * Potassium (K) slider input event listener / Kalium (K) Schieberegler Input Event Listener
 * 
 * @event input
 * @description Triggers continuously as the user drags the potassium slider
 * 
 * Functionality / Funktionalität:
 * Controls potassium concentration in the hydroponic solution.
 * 
 * Slider Range / Schiebereglerbereich:
 * 0-250 PPM (defined in HTML: min="0" max="250")
 * 
 * Agricultural Note / Landwirtschaftlicher Hinweis:
 * Potassium has the highest typical concentration in NPK ratios,
 * hence the larger range (0-250 vs 0-150 for P).
 * 
 * @callback
 * @param {Event} e - The input event object
 * @param {HTMLInputElement} e.target - The slider element
 * @param {string} e.target.value - Current slider value (0-250)
 * @returns {void}
 */
kSlider.addEventListener('input', (e) => {
    /**
     * Send potassium control command / Sendet Kalium-Steuerungsbefehl
     * 
     * Maintains consistent message protocol with other nutrient controls.
     */
    ws.send(JSON.stringify({
        type: 'nutrientControl',
        nutrient: 'potassium',
        value: e.target.value
    }));
});

/**
 * ============================================================================
 * NUTRIENT DOSING BUTTON EVENT LISTENERS / NÄHRSTOFFDOSIERUNGS-BUTTON-EVENT-LISTENER
 * ============================================================================
 * 
 * This section implements manual nutrient dosing controls via button clicks.
 * Each button triggers an immediate fixed-volume dose of a specific nutrient.
 * 
 * Diese Sektion implementiert manuelle Nährstoffdosierungssteuerungen über Button-Klicks.
 * 
 * Use Case / Anwendungsfall:
 * Manual dosing provides quick adjustments without using sliders.
 * Useful for:
 * - Emergency corrections
 * - Testing and calibration
 * - Quick top-ups during feeding schedules
 * 
 * Technical Reference / Technische Referenz:
 * - Click event: https://developer.mozilla.org/en-US/docs/Web/API/Element/click_event
 * - Button element: https://developer.mozilla.org/en-US/docs/Web/HTML/Element/button
 */

/**
 * Nitrogen (N) dose button click listener / Stickstoff (N) Dosierungs-Button Klick-Listener
 * 
 * @event click
 * @description Triggers when user clicks the nitrogen dose button
 * 
 * Event Type: 'click' / Ereignistyp: 'click'
 * - Fires when button is pressed and released
 * - Also triggered by keyboard (Enter/Space) for accessibility
 * 
 * Accessibility / Barrierefreiheit:
 * Button elements are keyboard accessible by default, supporting
 * users who cannot use a mouse (WCAG 2.1 compliance).
 * Reference: https://www.w3.org/WAI/WCAG21/Understanding/keyboard
 * 
 * @callback
 * @returns {void}
 */
document.getElementById('n-dose').addEventListener('click', () => {
    /**
     * Send nitrogen dose command / Sendet Stickstoff-Dosierungsbefehl
     * 
     * Message Structure / Nachrichtenstruktur:
     * {
     *   "type": "nutrientDose",      // Command type for immediate dosing
     *   "nutrient": "nitrogen",       // Target nutrient
     *   "amount": 5                   // Fixed dose amount in milliliters
     * }
     * 
     * Dosing Volume / Dosierungsvolumen:
     * 5ml of concentrated nitrogen solution
     * 
     * Hardware Implementation / Hardware-Implementierung:
     * The server translates this command to:
     * 1. Activate the nitrogen peristaltic pump
     * 2. Run for calculated duration to dispense 5ml
     * 3. Stop pump and confirm dose completion
     * 
     * Safety Considerations / Sicherheitsüberlegungen:
     * - Fixed amounts prevent accidental overdosing
     * - Server should implement cooldown periods between doses
     * - Maximum daily dosing limits should be enforced
     * 
     * Reference: Peristaltic pumps in hydroponics
     * https://en.wikipedia.org/wiki/Peristaltic_pump
     */
    ws.send(JSON.stringify({
        type: 'nutrientDose',
        nutrient: 'nitrogen',
        amount: 5
    }));
});

/**
 * Phosphorus (P) dose button click listener / Phosphor (P) Dosierungs-Button Klick-Listener
 * 
 * @event click
 * @description Triggers when user clicks the phosphorus dose button
 * 
 * Dosing Volume / Dosierungsvolumen:
 * 3ml of concentrated phosphorus solution
 * 
 * Rationale / Begründung:
 * Lower dose amount (3ml vs 5ml) reflects typical NPK ratios where
 * phosphorus requirements are lower than nitrogen.
 * 
 * Common NPK Ratios / Gängige NPK-Verhältnisse:
 * - Vegetative growth: 3-1-2 (N-P-K)
 * - Flowering: 1-2-2 (N-P-K)
 * 
 * Reference: NPK ratios for different growth stages
 * https://en.wikipedia.org/wiki/Fertilizer#NPK_rating
 * 
 * @callback
 * @returns {void}
 */
document.getElementById('p-dose').addEventListener('click', () => {
    /**
     * Send phosphorus dose command / Sendet Phosphor-Dosierungsbefehl
     * 
     * 3ml dose is appropriate for typical hydroponic concentrations.
     * Prevents phosphorus toxicity which can lock out other nutrients.
     */
    ws.send(JSON.stringify({
        type: 'nutrientDose',
        nutrient: 'phosphorus',
        amount: 3
    }));
});

/**
 * Potassium (K) dose button click listener / Kalium (K) Dosierungs-Button Klick-Listener
 * 
 * @event click
 * @description Triggers when user clicks the potassium dose button
 * 
 * Dosing Volume / Dosierungsvolumen:
 * 7ml of concentrated potassium solution
 * 
 * Rationale / Begründung:
 * Higher dose amount (7ml) reflects potassium's role as the most
 * abundant macronutrient in most plant growth stages.
 * 
 * Potassium Functions / Kaliumfunktionen:
 * - Regulates stomatal opening (water loss control)
 * - Activates enzymes for metabolism
 * - Improves disease resistance
 * - Enhances fruit quality and shelf life
 * 
 * Reference: Potassium in plant nutrition
 * https://en.wikipedia.org/wiki/Potassium#Biological_role
 * 
 * @callback
 * @returns {void}
 */
document.getElementById('k-dose').addEventListener('click', () => {
    /**
     * Send potassium dose command / Sendet Kalium-Dosierungsbefehl
     * 
     * 7ml dose reflects higher potassium requirements in hydroponic systems.
     */
    ws.send(JSON.stringify({
        type: 'nutrientDose',
        nutrient: 'potassium',
        amount: 7
    }));
});

/**
 * ============================================================================
 * LIGHT CONTROL EVENT LISTENER / LICHTSTEUERUNGS-EVENT-LISTENER
 * ============================================================================
 * 
 * This section implements grow light control via a toggle switch.
 * Controls the ON/OFF state of LED grow lights in the hydroponic system.
 * 
 * Diese Sektion implementiert Pflanzenlichtsteuerung über einen Umschalter.
 * 
 * Technical Reference / Technische Referenz:
 * - Change event: https://developer.mozilla.org/en-US/docs/Web/API/HTMLElement/change_event
 * - Checkbox input: https://developer.mozilla.org/en-US/docs/Web/HTML/Element/input/checkbox
 * 
 * Grow Lights in Hydroponics / Pflanzenlichter in Hydroponik:
 * - LED grow lights provide specific wavelengths for photosynthesis
 * - Red light (600-700nm): Promotes flowering and fruiting
 * - Blue light (400-500nm): Encourages vegetative growth
 * - Photoperiod control is crucial for plant development
 * 
 * Reference: LED grow lights
 * https://en.wikipedia.org/wiki/Grow_light#LED_grow_lights
 */

/**
 * Light toggle change event listener / Lichtschalter Änderungs-Event-Listener
 * 
 * @event change
 * @description Triggers when the light toggle switch changes state
 * 
 * Event Type: 'change' / Ereignistyp: 'change'
 * - Fires when checkbox state changes (checked/unchecked)
 * - Fires after user interaction is complete (unlike 'input')
 * 
 * Why 'change' instead of 'input'? / Warum 'change' statt 'input'?
 * For checkboxes, 'change' is the standard event that fires on state toggle.
 * 'input' would fire too frequently and is not typically used for checkboxes.
 * 
 * Reference: Change event on checkboxes
 * https://developer.mozilla.org/en-US/docs/Web/API/HTMLElement/change_event
 * 
 * @callback
 * @param {Event} e - The change event object
 * @param {HTMLInputElement} e.target - The checkbox element that triggered the event
 * @param {boolean} e.target.checked - The new state (true=ON, false=OFF)
 * @returns {void}
 */
lightToggle.addEventListener('change', (e) => {
    /**
     * Send light control command to server / Sendet Lichtsteuerungsbefehl an Server
     * 
     * Message Structure / Nachrichtenstruktur:
     * {
     *   "type": "lightControl",      // Command type identifier
     *   "state": true/false           // Desired light state (boolean)
     * }
     * 
     * Boolean State / Boolescher Zustand:
     * - true: Turn lights ON
     * - false: Turn lights OFF
     * 
     * e.target.checked property:
     * - Returns true when checkbox is checked
     * - Returns false when checkbox is unchecked
     * 
     * Hardware Control Flow / Hardware-Steuerungsablauf:
     * 1. Client sends command via WebSocket
     * 2. Server receives and validates command
     * 3. Server sends signal to relay or smart switch
     * 4. Relay switches power to LED grow lights
     * 5. Server broadcasts new state to all connected clients
     * 6. UI updates to reflect actual hardware state
     * 
     * Safety Features / Sicherheitsmerkmale:
     * - Command should include timestamp for logging
     * - Server should implement cooldown to prevent rapid switching
     * - Emergency stop functionality should be available
     * 
     * Power Management / Energieverwaltung:
     * Grow lights typically consume significant power (50-200W+).
     * Automated schedules can optimize energy usage and simulate
     * natural day/night cycles for plant health.
     */
    ws.send(JSON.stringify({
        type: 'lightControl',
        state: e.target.checked
    }));
    
    /**
     * Update light status display immediately / Aktualisiert Lichtstatusanzeige sofort
     * 
     * Optimistic UI Update / Optimistische UI-Aktualisierung:
     * Updates the status text before receiving server confirmation.
     * This provides immediate visual feedback for better user experience.
     * 
     * Ternary Operator / Ternärer Operator:
     * Syntax: condition ? valueIfTrue : valueIfFalse
     * 
     * Logic / Logik:
     * If e.target.checked is true → Set text to "ON"
     * If e.target.checked is false → Set text to "OFF"
     * 
     * Alternative Implementation / Alternative Implementierung:
     * Could wait for server confirmation before updating UI:
     * Pros: More accurate (reflects actual hardware state)
     * Cons: Slower perceived response, worse UX
     * 
     * Current approach is better for perceived performance while
     * relying on server's broadcast message to correct any discrepancies.
     * 
     * Design Pattern / Entwurfsmuster:
     * Optimistic UI - Update UI immediately, then reconcile with server state.
     * Common in modern web applications for responsive user experience.
     * 
     * Reference: Optimistic UI patterns
     * https://www.apollographql.com/docs/react/performance/optimistic-ui/
     */
    lightStatus.textContent = e.target.checked ? "ON" : "OFF";
});

/**
 * ============================================================================
 * PERIODIC DATA REQUEST MECHANISM / PERIODISCHER DATENANFORDERUNGSMECHANISMUS
 * ============================================================================
 * 
 * This section implements automatic polling of sensor data from the server.
 * Requests fresh data every 2 seconds to keep the dashboard updated in real-time.
 * 
 * Diese Sektion implementiert automatisches Polling von Sensordaten vom Server.
 * 
 * Technical Reference / Technische Referenz:
 * - setInterval(): https://developer.mozilla.org/en-US/docs/Web/API/setInterval
 * - WebSocket readyState: https://developer.mozilla.org/en-US/docs/Web/API/WebSocket/readyState
 * 
 * Architecture Pattern / Architekturmuster:
 * Polling Pattern - Client periodically requests data from server.
 * 
 * Alternative Approaches / Alternative Ansätze:
 * 1. Push Model: Server automatically sends updates (more efficient)
 * 2. Polling Model: Client requests updates at intervals (current implementation)
 * 3. Hybrid: Server pushes on change, client polls as backup
 * 
 * Current implementation uses polling for simplicity and reliability.
 */

/**
 * Set up periodic data request interval / Richtet periodisches Datenanforderungsintervall ein
 * 
 * @function setInterval
 * @description Executes a callback function repeatedly at specified time intervals
 * 
 * Parameters / Parameter:
 * @param {Function} callback - Function to execute on each interval
 * @param {number} delay - Time between executions in milliseconds (2000ms = 2 seconds)
 * 
 * Return Value / Rückgabewert:
 * @returns {number} intervalId - Unique identifier for the interval timer
 * 
 * Timer Management / Zeitverwaltung:
 * setInterval() creates a repeating timer. It can be stopped with:
 * clearInterval(intervalId)
 * 
 * Reference: Timers in JavaScript
 * https://developer.mozilla.org/en-US/docs/Learn/JavaScript/Asynchronous/Timeouts_and_intervals
 * 
 * Memory Considerations / Speicherüberlegungen:
 * In a production app, clear this interval when:
 * - User navigates away from page
 * - WebSocket connection is permanently closed
 * - Application is shutting down
 * 
 * Implementation / Implementierung:
 * window.addEventListener('beforeunload', () => clearInterval(intervalId));
 */
setInterval(() => {
    /**
     * Check WebSocket connection state / Überprüft WebSocket-Verbindungszustand
     * 
     * WebSocket.readyState property / WebSocket.readyState Eigenschaft:
     * Indicates the current state of the WebSocket connection.
     * 
     * Possible Values / Mögliche Werte:
     * - WebSocket.CONNECTING (0): Connection not yet established
     * - WebSocket.OPEN (1): Connection is open and ready to communicate
     * - WebSocket.CLOSING (2): Connection is in the process of closing
     * - WebSocket.CLOSED (3): Connection is closed or couldn't be opened
     * 
     * Why check readyState? / Warum readyState überprüfen?
     * Attempting to send data on a non-OPEN WebSocket throws an error:
     * "InvalidStateError: The connection has not been established"
     * 
     * This check prevents errors during:
     * - Initial connection establishment
     * - Network interruptions
     * - Server maintenance/restarts
     * - Connection closure
     * 
     * Reference: WebSocket readyState
     * https://developer.mozilla.org/en-US/docs/Web/API/WebSocket/readyState
     * 
     * Strict Equality / Strikte Gleichheit:
     * Uses === to compare without type coercion (best practice).
     */
    if (ws.readyState === WebSocket.OPEN) {
        /**
         * Send data request command to server / Sendet Datenanforderungsbefehl an Server
         * 
         * Message Structure / Nachrichtenstruktur:
         * {
         *   "type": "requestData"      // Command to request fresh sensor readings
         * }
         * 
         * Server Response / Serverantwort:
         * Upon receiving this request, the server should:
         * 1. Query current sensor values from IoT devices
         * 2. Package data into a 'sensorData' message
         * 3. Broadcast to this client (or all clients)
         * 
         * Example Response / Beispielantwort:
         * {
         *   "type": "sensorData",
         *   "temperature": 22.5,
         *   "ph": 6.2,
         *   "waterLevel": 85,
         *   "nitrogen": 120,
         *   "phosphorus": 45,
         *   "potassium": 180,
         *   "lightsOn": true,
         *   "timestamp": 1699721234567
         * }
         * 
         * Polling Interval / Polling-Intervall:
         * 2000ms (2 seconds) is chosen as a balance between:
         * - Responsiveness: Fast enough to detect changes quickly
         * - Efficiency: Not so fast as to overwhelm server/network
         * - Sensor update rate: Most sensors update every 1-5 seconds
         * 
         * Optimization Opportunities / Optimierungsmöglichkeiten:
         * - Adjust interval based on connection quality
         * - Increase interval when values are stable (adaptive polling)
         * - Use exponential backoff during network issues
         * - Implement server-sent events (SSE) for push-based updates
         * 
         * Network Efficiency / Netzwerkeffizienz:
         * This creates ~30 requests per minute per client.
         * For multiple clients, consider:
         * - Server-side caching of sensor values
         * - Broadcasting updates to all clients simultaneously
         * - Using MQTT or other IoT protocols for device communication
         * 
         * Reference: WebSocket vs Polling
         * https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API
         */
        ws.send(JSON.stringify({
            type: 'requestData'
        }));
    }
    /**
     * Implicit else / Implizite Else-Bedingung:
     * If WebSocket is not OPEN, do nothing this cycle.
     * The timer will try again in 2 seconds.
     * 
     * Error Handling Strategy / Fehlerbehandlungsstrategie:
     * Silent failure during disconnection is acceptable here because:
     * - The connection status is already displayed to the user
     * - The ws.onopen handler will restore functionality when reconnected
     * - No user action is required during temporary disconnections
     * 
     * Future Enhancement / Zukünftige Verbesserung:
     * Could implement automatic reconnection logic:
     * if (ws.readyState === WebSocket.CLOSED) {
     *     ws = new WebSocket(`ws://${window.location.hostname}:3000`);
     * }
     */
}, 2000); // Execute every 2000 milliseconds (2 seconds) / Alle 2000 Millisekunden ausführen (2 Sekunden)

/**
 * ============================================================================
 * END OF FILE / DATEIENDE
 * ============================================================================
 * 
 * File Summary / Dateizusammenfassung:
 * This file implements the client-side application logic for a hydroponic
 * system control dashboard. It provides real-time monitoring and control of:
 * - Environmental parameters (temperature, pH, water level)
 * - NPK nutrients (nitrogen, phosphorus, potassium)
 * - Grow lights (ON/OFF control)
 * 
 * Communication Protocol / Kommunikationsprotokoll:
 * Uses WebSocket for bidirectional, real-time communication between
 * the web client and the server/IoT backend.
 * 
 * Technology Stack / Technologie-Stack:
 * - Vanilla JavaScript (ES6+)
 * - WebSocket API (native browser API)
 * - DOM API for UI manipulation
 * - JSON for data serialization
 * 
 * Browser Compatibility / Browser-Kompatibilität:
 * - Chrome 16+ ✓
 * - Firefox 11+ ✓
 * - Safari 7+ ✓
 * - Edge (all versions) ✓
 * - Internet Explorer 10+ ✓ (with limitations)
 * 
 * References / Referenzen:
 * - MDN Web Docs: https://developer.mozilla.org/
 * - W3C WebSocket Specification: https://www.w3.org/TR/websockets/
 * - Hydroponics: https://en.wikipedia.org/wiki/Hydroponics
 * - JSON: https://www.json.org/
 * 
 * Author Notes / Autorennotizen:
 * Comments designed for project documentation and educational purposes.
 * All technical references provided to avoid copyright issues.
 * Bilingual comments (English/German) for international collaboration.
 * 
 * License / Lizenz:
 * (Add your project license here)
 * 
 * Last Updated / Zuletzt aktualisiert:
 * 2024-11-01
 */