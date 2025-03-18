class AnalogClock {
    constructor(canvasId) {
      // Grab the canvas and context
      this.canvas = document.getElementById(canvasId);
      this.ctx = this.canvas.getContext("2d");
  
      // Calculate basic geometry
      this.width = this.canvas.width;
      this.height = this.canvas.height;
      // Radius is half of the smaller dimension so the clock fits in the canvas
      this.radius = Math.min(this.width, this.height) / 2;
      // Center coordinates
      this.center = { x: this.width / 2, y: this.height / 2 };
  
      // Roman numerals (including watchmaker’s "IIII")
      this.romanNumerals = [
        "XII", "I", "II", "III", "IIII", 
        "V",   "VI","VII","VIII","IX", 
        "X",   "XI"
      ];
  
      // Start drawing immediately, then update every second
      this.drawClock();
      this.timer = setInterval(() => this.drawClock(), 1000);
    }
  
    // Convert degrees to radians
    toRadians(deg) {
      return (Math.PI / 180) * deg;
    }
  
    // Helper to draw circles
    drawCircle(x, y, radius, fillStyle, strokeStyle, lineWidth = 1) {
      this.ctx.beginPath();
      this.ctx.arc(x, y, radius, 0, 2 * Math.PI);
      if (fillStyle) {
        this.ctx.fillStyle = fillStyle;
        this.ctx.fill();
      }
      if (strokeStyle) {
        this.ctx.strokeStyle = strokeStyle;
        this.ctx.lineWidth = lineWidth;
        this.ctx.stroke();
      }
      this.ctx.closePath();
    }
  
    // Draw the static clock face
    drawClockFace() {
      // Outer border
      this.drawCircle(this.center.x, this.center.y, this.radius - 10, null, "#fff", 4);
  
      // Minute ticks (60 marks, 6 degrees apart)
      for (let i = 0; i < 60; i++) {
        const angle = this.toRadians(i * 6); 
        // Longer tick every 5 minutes
        const tickLength = (i % 5 === 0) ? 20 : 10; 
        const tickStart = this.radius - 15;
        const tickEnd = this.radius - 15 - tickLength;
  
        const startX = this.center.x + tickStart * Math.sin(angle);
        const startY = this.center.y - tickStart * Math.cos(angle);
        const endX   = this.center.x + tickEnd   * Math.sin(angle);
        const endY   = this.center.y - tickEnd   * Math.cos(angle);
  
        this.ctx.beginPath();
        this.ctx.moveTo(startX, startY);
        this.ctx.lineTo(endX, endY);
        this.ctx.strokeStyle = "#fff";
        this.ctx.lineWidth = (i % 5 === 0) ? 3 : 1.5;
        this.ctx.stroke();
        this.ctx.closePath();
      }
    }
  
    // Draw the Roman numerals
    drawNumerals() {
      this.ctx.fillStyle = "#fff";
      this.ctx.font = "bold 32px serif";
      this.ctx.textAlign = "center";
      this.ctx.textBaseline = "middle";
  
      // Each numeral is 30 degrees apart; offset so 12 is at the top (-90 degrees)
      for (let i = 0; i < 12; i++) {
        const angle = this.toRadians((i * 30) - 90);
        const x = this.center.x + Math.cos(angle) * (this.radius - 60);
        const y = this.center.y + Math.sin(angle) * (this.radius - 60);
        this.ctx.fillText(this.romanNumerals[i], x, y);
      }
    }
  
    // Draw hour, minute, and second hands
    drawHands(hours, minutes, seconds) {
      // Calculate angles for each hand
      // Hour hand: 30 deg per hour + 0.5 deg per minute
      const hourAngle = this.toRadians(
        (hours % 12) * 30 + (minutes / 60) * 30 - 90
      );
      // Minute hand: 6 deg per minute
      const minuteAngle = this.toRadians(minutes * 6 - 90);
      // Second hand: 6 deg per second
      const secondAngle = this.toRadians(seconds * 6 - 90);
  
      // Hour hand
      this.ctx.beginPath();
      this.ctx.strokeStyle = "#fff";
      this.ctx.lineWidth = 8;
      this.ctx.moveTo(this.center.x, this.center.y);
      this.ctx.lineTo(
        this.center.x + Math.cos(hourAngle) * (this.radius * 0.5),
        this.center.y + Math.sin(hourAngle) * (this.radius * 0.5)
      );
      this.ctx.stroke();
      this.ctx.closePath();
  
      // Minute hand
      this.ctx.beginPath();
      this.ctx.strokeStyle = "rgba(255, 160, 0, 0.9)";
      this.ctx.lineWidth = 6;
      this.ctx.moveTo(this.center.x, this.center.y);
      this.ctx.lineTo(
        this.center.x + Math.cos(minuteAngle) * (this.radius * 0.8),
        this.center.y + Math.sin(minuteAngle) * (this.radius * 0.8)
      );
      this.ctx.stroke();
      this.ctx.closePath();
  
      // Second hand
      this.ctx.beginPath();
      this.ctx.strokeStyle = "#ff0000";
      this.ctx.lineWidth = 2;
      this.ctx.moveTo(this.center.x, this.center.y);
      this.ctx.lineTo(
        this.center.x + Math.cos(secondAngle) * (this.radius * 0.9),
        this.center.y + Math.sin(secondAngle) * (this.radius * 0.9)
      );
      this.ctx.stroke();
      this.ctx.closePath();
  
      // Center cap
      this.drawCircle(this.center.x, this.center.y, 6, "#ff0000", null, 0);
    }
  
    // Pull it all together to draw the complete clock
    drawClock() {
      // Clear the canvas each frame
      this.ctx.clearRect(0, 0, this.width, this.height);
  
      // Draw static parts
      this.drawClockFace();
      this.drawNumerals();
  
      // Get the current time
      const now = new Date();
      const hours = now.getHours();
      const minutes = now.getMinutes();
      const seconds = now.getSeconds();
  
      // Draw the moving hands
      this.drawHands(hours, minutes, seconds);
    }
  }

