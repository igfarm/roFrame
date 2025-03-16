class AnalogClock {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext("2d");
        this.radius = this.canvas.width / 2;
        this.ctx.translate(this.radius, this.radius);
        this.radius *= 0.9;
        this.startClock();
    }

    drawClock() {
        this.ctx.clearRect(-this.radius, -this.radius, this.canvas.width, this.canvas.height);
        this.drawFace();
        this.drawNumbers();
        this.drawTime();
    }

    drawFace() {
        this.ctx.beginPath();
        this.ctx.arc(0, 0, this.radius, 0, 2 * Math.PI);
        this.ctx.fillStyle = "black";
        this.ctx.fill();
        this.ctx.lineWidth = 10;
        this.ctx.strokeStyle = "white";
        this.ctx.stroke();
        
        this.ctx.beginPath();
        this.ctx.arc(0, 0, 5, 0, 2 * Math.PI);
        this.ctx.fillStyle = "white";
        this.ctx.fill();
    }

    drawNumbers() {
        const romanNumerals = ["XII", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI"];
        this.ctx.font = `${this.radius * 0.15}px serif`;
        this.ctx.textBaseline = "middle";
        this.ctx.textAlign = "center";
        this.ctx.fillStyle = "white";
        for (let num = 1; num <= 12; num++) {
            let ang = (num * Math.PI) / 6;
            let x = this.radius * 0.85 * Math.cos(ang - Math.PI / 2);
            let y = this.radius * 0.85 * Math.sin(ang - Math.PI / 2);
            this.ctx.fillText(romanNumerals[num - 1], x, y);
        }
    }

    drawHand(pos, length, width, color) {
        this.ctx.beginPath();
        this.ctx.lineWidth = width;
        this.ctx.lineCap = "round";
        this.ctx.strokeStyle = color;
        this.ctx.moveTo(0, 0);
        this.ctx.lineTo(length * Math.cos(pos - Math.PI / 2), length * Math.sin(pos - Math.PI / 2));
        this.ctx.stroke();
    }

    drawTime() {
        const now = new Date();
        let hour = now.getHours() % 12;
        let minute = now.getMinutes();
        let second = now.getSeconds();

        hour = (hour * Math.PI) / 6 + (minute * Math.PI) / 360;
        this.drawHand(hour, this.radius * 0.5, 12, "white");

        minute = (minute * Math.PI) / 30 + (second * Math.PI) / 1800;
        this.drawHand(minute, this.radius * 0.7, 8, "white");

        second = (second * Math.PI) / 30;
        this.drawHand(second, this.radius * 0.8, 2, "red");
    }

    startClock() {
        setInterval(() => this.drawClock(), 1000);
        console.log('tick tock')
    }
}

window.onload = function () {
    const clockContainer = document.getElementById("clockContainer");
    const canvas = document.createElement("canvas");
    canvas.id = "clockCanvas";
    canvas.width = 600;
    canvas.height = 600;
    canvas.style.display = "block";
    canvas.style.margin = "0 auto";
    clockContainer.appendChild(canvas);
    new AnalogClock("clockCanvas");
    console.log('AnalogClock')
};
