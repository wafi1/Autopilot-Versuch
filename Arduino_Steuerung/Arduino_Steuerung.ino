#include <Wire.h>

const int pwmPin = 6;     // PWM Pin für LED (Motor simuliert)
const int dirPin1 = A2;   // Richtungspin 1 für LED
const int dirPin2 = A1;   // Richtungspin 2 für LED

volatile byte command = 0;       // Globaler Speicher für den letzten Befehl
volatile byte pwmValue = 0;      // Globaler Speicher für den letzten PWM-Wert
volatile byte direction = 0;     // Globaler Speicher für die letzte Richtung
volatile bool newData = false;   // Flag für neue Daten

void setup() {
  Serial.begin(9600);
  Wire.begin(0x21);               // I2C-Adresse des Arduino als Slave
  Wire.onReceive(receiveData);    // Interrupt bei empfangenen Daten

  pinMode(pwmPin, OUTPUT);
  pinMode(dirPin1, OUTPUT);
  pinMode(dirPin2, OUTPUT);

  digitalWrite(pwmPin, LOW);
  digitalWrite(dirPin1, LOW);
  digitalWrite(dirPin2, LOW);

  Serial.println("I2C Slave Initialized");
}

void loop() {
  // Datenverarbeitung außerhalb des Interrupts
  if (newData) {
    newData = false; // Flag zurücksetzen

    Serial.print("Empfangener Befehl: ");
    Serial.println(command);

    if (command == 1) {  // PWM-Steuerung
      Serial.print("PWM-Wert: ");
      Serial.println(pwmValue);
      Serial.print("Richtung: ");
      Serial.println(direction);

      if (pwmValue == 0) {
        // Stop: Alle Pins auf LOW setzen
        digitalWrite(dirPin1, LOW);
        digitalWrite(dirPin2, LOW);
        digitalWrite(pwmPin, LOW);
        Serial.println("Motor Stopp: Alle Pins auf LOW");
      } else {
        // PWM setzen
        analogWrite(pwmPin, pwmValue);

        // Richtung setzen
        if (direction == 1) {
          digitalWrite(dirPin1, HIGH);
          digitalWrite(dirPin2, LOW);
          Serial.println("Vorwärts: LED A2 an, LED A1 aus");
        } else if (direction == 2) {
          digitalWrite(dirPin1, LOW);
          digitalWrite(dirPin2, HIGH);
          Serial.println("Rückwärts: LED A1 an, LED A2 aus");
        } else {
          digitalWrite(dirPin1, LOW);
          digitalWrite(dirPin2, LOW);
          Serial.println("Ungültige Richtung: Alle Pins auf LOW");
        }
      }
    } else {
      digitalWrite(dirPin1, LOW);
      digitalWrite(dirPin2, LOW);
      Serial.println("Unbekannter Befehl: LEDs aus");
    }
  }
}

void receiveData(int byteCount) {
  // Sicherstellen, dass genug Daten empfangen wurden
  if (byteCount >= 3) {
    command = Wire.read();    // Erster Befehl
    pwmValue = Wire.read();   // PWM-Wert (0-255)
    direction = Wire.read();  // Richtung (1 oder 2)
    newData = true;           // Datenverarbeitung anstoßen
  } else {
    // Ungültige Daten: Alle LEDs ausschalten
    digitalWrite(pwmPin, LOW);
    digitalWrite(dirPin1, LOW);
    digitalWrite(dirPin2, LOW);
    Serial.println("Ungültige Daten empfangen!");
  }
}
