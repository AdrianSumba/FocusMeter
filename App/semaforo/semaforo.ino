#include <LiquidCrystal.h>

const int ledRojo = A5;
const int ledAmarillo = A4;
const int ledVerde = A3;
const int alertaSonora = A2;

LiquidCrystal lcd(12, 11, 5, 4, 3, 2);

const int ATENCION_BAJA  = 0;
const int ATENCION_MEDIA = 1;
const int ATENCION_ALTA  = 2;

int nivelAtencionAnterior = -1;

unsigned long ultimoDatoMillis = 0;
const unsigned long TIMEOUT_MS = 5000;
bool datoValido = false;

void apagarLeds() {
  digitalWrite(ledRojo, LOW);
  digitalWrite(ledAmarillo, LOW);
  digitalWrite(ledVerde, LOW);
}

void setup() {
  pinMode(ledRojo, OUTPUT);
  pinMode(ledAmarillo, OUTPUT);
  pinMode(ledVerde, OUTPUT);
  pinMode(alertaSonora, OUTPUT);

  lcd.begin(16, 2);
  Serial.begin(115200);

  apagarLeds();
  
  lcd.setCursor(0, 0);
  lcd.print("Sin datos");
  lcd.setCursor(0, 1);
  lcd.print("esperando...");
}

void loop() {
  unsigned long ahora = millis();

  if (Serial.available()) {
    String dato = Serial.readStringUntil('\n');
    dato.trim();

    if (dato.startsWith("<") && dato.endsWith(">")) {
      dato = dato.substring(1, dato.length() - 1);
      float valor = dato.toFloat();

      if (valor >= 0.0 && valor <= 100.0) {
        ultimoDatoMillis = ahora;
        datoValido = true;

        int nivelAtencionActual;

        if (valor >= 80.0) {
          digitalWrite(ledVerde, HIGH);
          digitalWrite(ledAmarillo, LOW);
          digitalWrite(ledRojo, LOW);
          nivelAtencionActual = ATENCION_ALTA;

        } else if (valor >= 70.0) {
          digitalWrite(ledVerde, LOW);
          digitalWrite(ledAmarillo, HIGH);
          digitalWrite(ledRojo, LOW);
          nivelAtencionActual = ATENCION_MEDIA;

        } else {
          digitalWrite(ledVerde, LOW);
          digitalWrite(ledAmarillo, LOW);
          digitalWrite(ledRojo, HIGH);
          nivelAtencionActual = ATENCION_BAJA;
        }

        lcd.clear();
        lcd.setCursor(0, 0);
        lcd.print("Estimacion de");
        lcd.setCursor(0, 1);
        lcd.print("atencion: ");
        lcd.print(valor, 2);
        lcd.print("%");
        
        if (nivelAtencionActual != nivelAtencionAnterior) {
          tone(alertaSonora, 2000, 200);
          nivelAtencionAnterior = nivelAtencionActual;
        }
      }
    }
  }

  if (datoValido && (ahora - ultimoDatoMillis > TIMEOUT_MS)) {
    apagarLeds();
    lcd.setCursor(0, 0);
    lcd.print("Sin conexion!   ");
    lcd.setCursor(0, 1);
    lcd.print("                ");
    datoValido = false;
    nivelAtencionAnterior = -1;
  }
}