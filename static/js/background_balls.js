// some random colors
const colors = ["#e27e87", "#eddba5", "#ffffff"];

//number of balls to be created
const numBalls = 100;
const balls = [];

for (let i = 0; i < numBalls; i++) {
let ball = document.createElement("div");
ball.classList.add("ball");
ball.style.background = colors[Math.floor(Math.random() * colors.length)];
// change the direction of the ball vertically
ball.style.left = `${Math.floor(Math.random() * 95)}vw`;
// change the direction of the ball horizontally
ball.style.top = `${Math.floor(Math.random() * 50)}vh`;
ball.style.transform = `scale(${Math.random() * 10})`;
ball.style.width = `${Math.random()* 7}em`;
ball.style.height = ball.style.width;

balls.push(ball);
document.body.append(ball);
}

// Keyframes
balls.forEach((el, i, ra) => {
let to = {
    x: Math.random() * (i % 2 === 0 ? -10 : 10),
    y: Math.random() * 90
};

let anim = el.animate(
    [
    { transform: "translate(0, 0)" },
    { transform: `translate(${to.x}rem, ${to.y}rem)` }
    ],
    {
    duration: (Math.random() + 1) * 4000, // random duration
    direction: "alternate",
    fill: "both",
    iterations: Infinity,
    easing: "ease-in-out"
    }
);
});