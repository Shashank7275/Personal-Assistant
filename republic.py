import pygame
import math
import random
import sys
import time

# --- CONFIGURATION & CONSTANTS ---
WIDTH, HEIGHT = 1200, 800
FPS = 60
TITLE = "77th Republic Day Celebration"

# COLORS (R, G, B)
SAFFRON = (255, 153, 51)
WHITE = (255, 255, 255)
GREEN = (19, 136, 8)
NAVY_BLUE = (0, 0, 128)
BLACK = (10, 10, 15)  # Slightly non-black for depth
GOLD = (255, 215, 0)
CYAN_GLOW = (0, 255, 255)

# --- INITIALIZATION ---
pygame.init()
pygame.display.set_caption(TITLE)
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

# Attempt to load a nice font, fallback to default
def get_font(size, bold=False):
    fonts = ["segoeui", "calibri", "arial", "helvetica"]
    match = pygame.font.match_font(fonts)
    if match:
        f = pygame.font.Font(match, size)
        f.set_bold(bold)
        return f
    return pygame.font.SysFont("arial", size, bold=bold)

# --- HELPER CLASSES ---

class Particle:
    def __init__(self, x, y, color, target_type='ring', center=(WIDTH//2, HEIGHT//2)):
        self.x = x
        self.y = y
        self.origin_x = x
        self.origin_y = y
        self.color = color
        self.size = random.uniform(2, 4)
        self.target_type = target_type
        self.center = center
        
        # Physics
        self.angle = random.uniform(0, 2 * math.pi)
        self.radius = random.uniform(100, 250)
        self.speed = random.uniform(0.02, 0.05)
        self.drift_speed = random.uniform(0.5, 2.0)
        
        # Bloom/Glow alpha
        self.alpha = 255

    def update(self, t, phase):
        if phase == 'explode':
            # Move towards ring formation
            target_x = self.center[0] + math.cos(self.angle + t * self.speed) * self.radius
            target_y = self.center[1] + math.sin(self.angle + t * self.speed) * self.radius
            
            # Smooth lerp
            self.x += (target_x - self.x) * 0.05
            self.y += (target_y - self.y) * 0.05
            
        elif phase == 'float':
            # Upward drift for final scene
            self.y -= self.drift_speed
            self.x += math.sin(t + self.origin_y) * 0.5
            self.alpha = max(0, self.alpha - 0.5)

    def draw(self, surface):
        if self.alpha <= 0: return
        
        # Draw main particle
        s = pygame.Surface((int(self.size*2), int(self.size*2)), pygame.SRCALPHA)
        c = (*self.color, int(self.alpha))
        pygame.draw.circle(s, c, (int(self.size), int(self.size)), int(self.size))
        
        # Fake Glow (larger transparent circle)
        glow_size = int(self.size * 4)
        glow_c = (*self.color, int(self.alpha * 0.3))
        pygame.draw.circle(s, glow_c, (int(self.size), int(self.size)), glow_size)
        
        # Blitting with ADD blending for "light" effect
        surface.blit(s, (int(self.x) - self.size, int(self.y) - self.size))

class Flag:
    def __init__(self, x, y, w, h):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.stripe_h = h // 3
        
        # Pre-calculate points for particles later
        self.particles = []
        step = 8 # Density of particles
        
        for i in range(0, w, step):
            for j in range(0, h, step):
                # Determine color based on height
                if j < h // 3: color = SAFFRON
                elif j < 2 * h // 3: color = WHITE
                else: color = GREEN
                
                # Center chakra pixel approximation (rough)
                cy = h // 2
                cx = w // 2
                if abs(j - cy) < 25 and abs(i - cx) < 25:
                   if (i-cx)**2 + (j-cy)**2 < 25**2:
                       color = NAVY_BLUE

                self.particles.append(Particle(x + i, y + j, color))

    def draw_wave(self, surface, t):
        # Draw using vertical strips to simulate sine wave
        for i in range(0, self.w, 2):
            offset_y = math.sin(t * 3 + i * 0.02) * 15
            
            # Saffron
            pygame.draw.rect(surface, SAFFRON, (self.x + i, self.y + offset_y, 2, self.stripe_h))
            # White
            pygame.draw.rect(surface, WHITE, (self.x + i, self.y + self.stripe_h + offset_y, 2, self.stripe_h))
            # Green
            pygame.draw.rect(surface, GREEN, (self.x + i, self.y + 2 * self.stripe_h + offset_y, 2, self.stripe_h))
            
            # Center Chakra (Simple representation in wave)
            center_x = self.w // 2
            if abs(i - center_x) < 25:
                 cy = self.y + 1.5 * self.stripe_h + offset_y
                 pygame.draw.circle(surface, NAVY_BLUE, (self.x + i, int(cy)), 1)
    
    def get_particles(self):
        return self.particles

class AshokaChakra:
    def __init__(self, x, y, radius):
        self.x = x
        self.y = y
        self.radius = radius
        self.spokes = 24
        self.angle = 0
    
    def update(self):
        self.angle += 1

    def draw(self, surface, alpha=255):
        # Create a temporary surface for transparency
        s = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        cx, cy = self.radius, self.radius
        color = (*NAVY_BLUE, alpha)
        
        # Outer rim
        pygame.draw.circle(s, color, (cx, cy), self.radius, 2)
        pygame.draw.circle(s, color, (cx, cy), 5) # Hub
        
        # Spokes
        for i in range(self.spokes):
            theta = math.radians(self.angle + (360 / self.spokes) * i)
            end_x = cx + math.cos(theta) * (self.radius - 2)
            end_y = cy + math.sin(theta) * (self.radius - 2)
            pygame.draw.line(s, color, (cx, cy), (end_x, end_y), 1)
            
        surface.blit(s, (self.x - self.radius, self.y - self.radius))

def draw_text_centered(surface, text, font, y_pos, color, alpha, scale=1.0):
    text_surf = font.render(text, True, color)
    w, h = text_surf.get_size()
    
    # Scale if needed
    if scale != 1.0:
        new_w, new_h = int(w * scale), int(h * scale)
        text_surf = pygame.transform.smoothscale(text_surf, (new_w, new_h))
        w, h = new_w, new_h
        
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    s.blit(text_surf, (0, 0))
    s.set_alpha(alpha)
    
    rect = s.get_rect(center=(WIDTH // 2, y_pos))
    surface.blit(s, rect)
    
    # Subtle glow copy
    if alpha > 100:
        glow_s = pygame.transform.smoothscale(s, (w + 10, h + 10))
        glow_s.set_alpha(50)
        g_rect = glow_s.get_rect(center=(WIDTH // 2, y_pos))
        surface.blit(glow_s, g_rect)

# --- MAIN ANIMATION LOOP ---

def main():
    running = True
    start_time = time.time()
    
    # Objects
    flag = Flag(WIDTH//2 - 150, HEIGHT//2 - 100, 300, 200)
    chakra = AshokaChakra(WIDTH//2, HEIGHT//2, 100)
    particles = []
    
    # Fonts
    font_main = get_font(60, bold=True)
    font_sub = get_font(40)
    font_hind = get_font(80, bold=True) # Assuming system font handles UTF-8 or standard chars

    # States
    # 0-5s: Flag waving
    # 5-8s: Text 1
    # 8-12s: Particle explosion
    # 12-16s: Jai Hind
    # 16s+: Final fade
    
    bg_color = list(BLACK)

    while running:
        dt = clock.tick(FPS) / 1000.0
        current_time = time.time() - start_time
        t_val = current_time # Simple time variable for sines
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        # Clear Screen
        screen.fill(bg_color)
        
        # Background subtle gradients or rays can be added here
        # For now, keep it dark and clean as requested
        
        # --- SCENE LOGIC ---
        
        if current_time < 5.0:
            # Phase 1: Flag Waving
            # Fade in flag
            flag_alpha = min(255, current_time * 50) 
            flag.draw_wave(screen, t_val)
            
            # Initial instruction or title nicely fading
            if current_time > 1.0:
                alpha = min(255, (current_time - 1.0) * 80)
                draw_text_centered(screen, "77th Republic Day", font_sub, HEIGHT - 100, WHITE, alpha)

        elif current_time < 8.0:
            # Phase 2: Text "Happy Republic Day"
            flag.draw_wave(screen, t_val)
            
            # Text Animation
            text_t = current_time - 5.0
            scale = 1.0 + math.sin(text_t * 2) * 0.05
            alpha = min(255, text_t * 200)
            if text_t > 2.0: alpha = max(0, 255 - (text_t - 2.0) * 200) # Fade out
            
            draw_text_centered(screen, "Happy Republic Day", font_main, HEIGHT//2 - 150, GOLD, alpha, scale)

        elif current_time < 12.0:
            # Phase 3: Transition to Particles
            particle_t = current_time - 8.0
            
            if not particles:
                particles = flag.get_particles() # Generate once
            
            # Update and Draw Particles
            for p in particles:
                p.update(particle_t, phase='explode')
                p.draw(screen)
                
            # Chakra fading in background
            chakra_alpha = min(100, particle_t * 30)
            chakra.update()
            chakra.draw(screen, chakra_alpha)

        elif current_time < 18.0:
            # Phase 4: Jai Hind & Arc Reactor Style
            phase_t = current_time - 12.0
            
            # Particles continue spinning or drift
            for p in particles:
                p.update(phase_t, phase='explode') # Keep spinning in ring
                p.draw(screen)
            
            # Chakra full rotating
            chakra.update()
            chakra.draw(screen, 150)
            
            # "Jai Hind" Text with Pulse
            pulse = 1.0 + math.sin(phase_t * 5) * 0.1
            text_alpha = min(255, phase_t * 100)
            
            draw_text_centered(screen, "Jai Hind", font_hind, HEIGHT//2, SAFFRON, text_alpha, pulse)
            
            # Add Flag Emoji or small tricolor bars below text if font doesn't support emoji
            # Drawing simple bars below text
            bar_y = HEIGHT//2 + 60
            w_bar = 200 * pulse
            pygame.draw.rect(screen, SAFFRON, (WIDTH//2 - w_bar//2, bar_y, w_bar, 5))
            pygame.draw.rect(screen, WHITE, (WIDTH//2 - w_bar//2, bar_y + 5, w_bar, 5))
            pygame.draw.rect(screen, GREEN, (WIDTH//2 - w_bar//2, bar_y + 10, w_bar, 5))

        else:
            # Phase 5: Final Ascent
            final_t = current_time - 18.0
            
            # Particles drift up
            for p in particles:
                p.update(final_t, phase='float')
                p.draw(screen)
                
            # Fade out everything else
            # Camera zoom out effect simulation (shrink objects or fade)
            
            # Final Title
            draw_text_centered(screen, "Proud Indian", font_sub, HEIGHT - 50, WHITE, 200)
            
            # Draw static beams/rays
            # (Simulated by transparent polygons)
            s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            poly_points = [
                (WIDTH//2, HEIGHT),
                (WIDTH//2 - 100 - final_t*50, 0),
                (WIDTH//2 + 100 + final_t*50, 0)
            ]
            pygame.draw.polygon(s, (255, 255, 255, 20), poly_points)
            screen.blit(s, (0,0))

        pygame.display.flip()
        
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
