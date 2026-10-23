from manim import *

class Funnel(Scene):
    """3-step pipeline diagram + a growth curve, ~4s, transparent background."""
    def construct(self):
        steps = ["Plan", "Build", "Render"]
        boxes = VGroup(*[
            VGroup(RoundedRectangle(corner_radius=0.2, width=2.6, height=1.1, color=YELLOW, fill_opacity=0.15),
                   Text(s, font_size=36)) for s in steps
        ]).arrange(RIGHT, buff=1.0).shift(UP * 1.2)
        arrows = VGroup(*[Arrow(boxes[i].get_right(), boxes[i + 1].get_left(), buff=0.1, color=WHITE) for i in range(2)])
        self.play(LaggedStart(*[FadeIn(b, shift=UP * 0.3) for b in boxes], lag_ratio=0.3), run_time=1.2)
        self.play(*[GrowArrow(a) for a in arrows], run_time=0.5)
        ax = Axes(x_range=[0, 4, 1], y_range=[0, 16, 4], x_length=5, y_length=2.2, tips=False).shift(DOWN * 1.6)
        curve = ax.plot(lambda x: x ** 2, color=YELLOW)
        eq = MathTex(r"y = x^2", font_size=40).next_to(ax, RIGHT)
        self.play(Create(ax), run_time=0.5)
        self.play(Create(curve), Write(eq), run_time=1.0)
        self.wait(0.8)
