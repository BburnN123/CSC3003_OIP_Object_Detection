//Delare global variable
int motorpin1 = 2;
int motorpin2 = 3;
int fan1 = 4 ;
int fan2 = 5;
int UVlight = 6;
int Pump1 = 8;
int Valve1 = 9;
int inner_light_pin = 12;

//Step 1 is washing
//Step 2 is drying
//Step 3 is steralizing
String step1 = "wash";
String step2 = "dry";
String step3 = "ster";

void setup() {
  //Declare pinmode
  pinMode(motorpin1, OUTPUT);
  pinMode(motorpin2, OUTPUT);
  pinMode(fan1, OUTPUT);
  pinMode(fan2, OUTPUT);
  pinMode(UVlight, OUTPUT);
  pinMode(Pump1, OUTPUT);
  pinMode(Valve1, OUTPUT);
  Serial.begin(9600);
}
void loop() {
  //Serial communication from the Raspberry pi
  if(Serial.available() > 0 ) {
    String action = Serial.readStringUntil('\n');
    delay(500);
    Serial.print(action);
    //Washing
    if (action.equals(step1)){
      digitalWrite(motorpin1, HIGH); //motor rotate clockwise
      digitalWrite(motorpin2, LOW);
      delay(10000);
      digitalWrite(motorpin1, LOW); //motor stop rotating
      digitalWrite(motorpin2, LOW);
      digitalWrite(Valve1, LOW); //Valve closes
      digitalWrite(Pump1, HIGH); //Pump open
      delay(10000);
      digitalWrite(Pump1 , LOW); //Pump closes    
 }
    //Cleaning
    else if (action.equals(step2)) {
      digitalWrite(motorpin1, LOW); //motor rotate counter-clockwise
      digitalWrite(motorpin2, HIGH);
      digitalWrite(Valve1, HIGH); //Valve open
      delay(10000);
      digitalWrite(motorpin1, LOW); //motor stop
      digitalWrite(motorpin2, LOW);
      digitalWrite(inner_light_pin, HIGH); //LED turns on
      digitalWrite(fan1 , HIGH); //fan1 turns on
      digitalWrite(fan2 , HIGH); //fan2 turns on
      delay(10000);
  }
    //Sterlize process
    else if (action.equals(step3)){
      digitalWrite(fan1 , LOW); //fan1 turns off
      digitalWrite(fan2 , LOW); //fan2 turns off 
      digitalWrite(inner_light_pin, LOW); //LED turns off
      digitalWrite(UVlight , HIGH); //LED light strip turns on
      delay(10000);
      digitalWrite(UVlight , LOW); //LED light strip turns off
      delay(10000);
  }
   //End of process
     else if (action.equals("stop")){
       digitalWrite(UVlight , LOW);
  }
}
}
